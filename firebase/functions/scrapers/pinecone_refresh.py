"""
Monthly Pinecone vector DB refresh for Migravio RAG pipeline.

Re-ingests time-sensitive immigration data sources:
- DOS Visa Bulletin (changes monthly)
- USCIS Processing Times (changes quarterly)
- Federal Register rules (new rules continuously)

Stable sources (visa overviews, USCIS manual, forms, DOL wages) are NOT
refreshed here — they only change with manual updates.

Environment variables required:
- OPENROUTER_API_KEY
- PINECONE_API_KEY
- PINECONE_INDEX_NAME (default: immigration-docs)
"""

import hashlib
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any

import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
from pinecone import Pinecone

logger = logging.getLogger(__name__)

# --- Shared utilities (sync versions for Cloud Functions) ---


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by approximate token count."""
    words_per_chunk = int(chunk_size * 0.75)
    words_overlap = int(overlap * 0.75)
    words = text.split()

    if len(words) <= words_per_chunk:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + words_per_chunk
        chunks.append(" ".join(words[start:end]))
        start += words_per_chunk - words_overlap

    return chunks


def generate_vector_id(source: str, section: str) -> str:
    """Generate deterministic vector ID (same logic as scripts/shared.py)."""
    content = f"{source}::{section}"
    hash_digest = hashlib.sha256(content.encode()).hexdigest()
    return f"{source}_{hash_digest[:16]}"


def get_embedding_sync(client: OpenAI, text: str) -> list[float]:
    """Get embedding using synchronous OpenAI client via OpenRouter."""
    response = client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def upsert_chunks_sync(
    openai_client: OpenAI,
    pinecone_index,
    chunks: list[str],
    metadata_list: list[dict[str, Any]],
    source: str,
) -> int:
    """Chunk, embed, and upsert to Pinecone (synchronous)."""
    if not chunks:
        return 0

    vectors = []
    batch_size = 100

    for i, (chunk, metadata) in enumerate(zip(chunks, metadata_list)):
        try:
            embedding = get_embedding_sync(openai_client, chunk)
        except Exception as e:
            logger.error(f"Failed to embed chunk {i}: {e}")
            continue

        section_id = metadata.get("section", f"chunk_{i}")
        vector_id = generate_vector_id(source, section_id)
        metadata["text"] = chunk

        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata,
        })

        if len(vectors) >= batch_size:
            pinecone_index.upsert(vectors=vectors)
            logger.info(f"Upserted batch of {len(vectors)} vectors")
            vectors = []

    if vectors:
        pinecone_index.upsert(vectors=vectors)
        logger.info(f"Upserted final batch of {len(vectors)} vectors")

    return len(chunks)


# --- Visa Bulletin scraper ---

VISA_BULLETIN_URL = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html"


def scrape_visa_bulletin() -> list[dict[str, Any]]:
    """Scrape the current DOS Visa Bulletin and return chunks with metadata."""
    logger.info("Scraping DOS Visa Bulletin...")

    try:
        response = httpx.get(
            VISA_BULLETIN_URL,
            headers={"User-Agent": "Migravio Immigration Assistant (migravio.com)"},
            follow_redirects=True,
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch Visa Bulletin: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")

    # Find the latest bulletin link
    bulletin_link = None
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "visa-bulletin-for-" in href and "/visa-bulletin/" in href:
            bulletin_link = href
            break

    if not bulletin_link:
        logger.warning("Could not find current Visa Bulletin link")
        return []

    if bulletin_link.startswith("/"):
        bulletin_link = f"https://travel.state.gov{bulletin_link}"

    # Fetch the actual bulletin page
    try:
        response = httpx.get(
            bulletin_link,
            headers={"User-Agent": "Migravio Immigration Assistant (migravio.com)"},
            follow_redirects=True,
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch bulletin page: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")

    # Extract month/year from title
    title_tag = soup.find("h1")
    bulletin_title = title_tag.get_text(strip=True) if title_tag else "Current Visa Bulletin"

    # Extract tables
    tables = soup.find_all("table")
    content_items = []

    for table in tables:
        caption = table.find("caption")
        headers_row = table.find("tr")
        if not headers_row:
            continue

        headers = [th.get_text(strip=True) for th in headers_row.find_all(["th", "td"])]
        if len(headers) < 2:
            continue

        table_title = caption.get_text(strip=True) if caption else " | ".join(headers[:3])
        rows = table.find_all("tr")[1:]

        for row in rows:
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) < 2 or not cells[0]:
                continue

            category = cells[0]
            row_text = f"{bulletin_title} - {table_title}\n\nCategory: {category}\n"

            for j, header in enumerate(headers[1:], 1):
                if j < len(cells):
                    row_text += f"{header}: {cells[j]}\n"

            # Infer visa types
            visa_types = []
            cat_lower = category.lower()
            if "1st" in cat_lower or "eb-1" in cat_lower:
                visa_types.append("EB-1")
            if "2nd" in cat_lower or "eb-2" in cat_lower:
                visa_types.append("EB-2")
            if "3rd" in cat_lower or "eb-3" in cat_lower:
                visa_types.append("EB-3")
            if "f1" in cat_lower or "f-1" in cat_lower or "1st" in cat_lower:
                visa_types.append("Green Card")

            content_items.append({
                "content": row_text,
                "metadata": {
                    "source": "visa_bulletin",
                    "document_title": f"Visa Bulletin: {bulletin_title}",
                    "visa_types": visa_types or ["Green Card"],
                    "section": f"vb_{hashlib.md5(row_text.encode()).hexdigest()[:12]}",
                },
            })

    # Add explanatory context
    explanations = [
        {
            "content": (
                f"{bulletin_title} - How to Read the Visa Bulletin\n\n"
                "The Visa Bulletin is published monthly by the Department of State. "
                "It shows priority date cutoffs for immigrant visa categories. "
                "If your priority date is BEFORE the listed date, your category is 'current' "
                "and you may proceed with your immigrant visa or adjustment of status application. "
                "'C' means current (no backlog). 'U' means unavailable."
            ),
            "metadata": {
                "source": "visa_bulletin",
                "document_title": f"Visa Bulletin: How to Read - {bulletin_title}",
                "visa_types": ["Green Card", "EB-1", "EB-2", "EB-3"],
                "section": "vb_how_to_read",
            },
        },
        {
            "content": (
                f"{bulletin_title} - Final Action Dates vs Dates for Filing\n\n"
                "The bulletin contains two charts: Final Action Dates and Dates for Filing. "
                "Final Action Dates: Your priority date must be before this date for visa issuance. "
                "Dates for Filing: USCIS may allow filing based on these earlier dates. "
                "Check USCIS.gov monthly to see which chart they are accepting."
            ),
            "metadata": {
                "source": "visa_bulletin",
                "document_title": f"Visa Bulletin: Charts Explained - {bulletin_title}",
                "visa_types": ["Green Card", "EB-1", "EB-2", "EB-3"],
                "section": "vb_charts_explained",
            },
        },
    ]
    content_items.extend(explanations)

    logger.info(f"Extracted {len(content_items)} visa bulletin items")
    return content_items


# --- Processing Times (curated fallback) ---

PROCESSING_TIMES_DATA = {
    "I-485": {
        "form_name": "Application to Register Permanent Residence (Adjustment of Status)",
        "category": "Green Card",
        "times": {
            "Nebraska Service Center": "8.5-14 months",
            "Texas Service Center": "9-15.5 months",
            "National Benefits Center": "10-20.5 months",
        },
        "visa_types": ["Green Card", "EB-1", "EB-2", "EB-3"],
    },
    "I-130": {
        "form_name": "Petition for Alien Relative",
        "category": "Family-Based",
        "times": {
            "California Service Center": "5-12 months",
            "Nebraska Service Center": "5.5-13 months",
            "Texas Service Center": "6-14 months",
            "Potomac Service Center": "11-19 months",
        },
        "visa_types": ["Green Card"],
    },
    "I-140": {
        "form_name": "Immigrant Petition for Alien Workers",
        "category": "Employment-Based",
        "times": {
            "Nebraska Service Center": "6-12 months",
            "Texas Service Center": "6-9 months",
            "Premium Processing": "15 business days",
        },
        "visa_types": ["EB-1", "EB-2", "EB-3", "H-1B"],
    },
    "I-765": {
        "form_name": "Application for Employment Authorization (EAD)",
        "category": "Work Permit",
        "times": {
            "Nebraska Service Center": "3-5 months",
            "Potomac Service Center": "2-7 months",
            "Texas Service Center": "3-6 months",
        },
        "visa_types": ["OPT", "H-4", "Green Card"],
    },
    "I-131": {
        "form_name": "Application for Travel Document",
        "category": "Travel",
        "times": {
            "Nebraska Service Center": "5-9.5 months",
            "Texas Service Center": "6-10 months",
        },
        "visa_types": ["Green Card"],
    },
    "N-400": {
        "form_name": "Application for Naturalization",
        "category": "Citizenship",
        "times": {
            "National average": "5-8 months",
            "Field offices (busy)": "8-14.5 months",
        },
        "visa_types": ["Naturalization"],
    },
    "I-129": {
        "form_name": "Petition for Nonimmigrant Worker",
        "category": "Work Visa",
        "times": {
            "California Service Center": "2-6 months",
            "Vermont Service Center": "2-5 months",
            "Premium Processing": "15 business days",
        },
        "visa_types": ["H-1B", "L-1", "O-1"],
    },
    "I-539": {
        "form_name": "Application to Extend/Change Nonimmigrant Status",
        "category": "Status Change",
        "times": {
            "California Service Center": "5-10 months",
            "Vermont Service Center": "5.5-13 months",
        },
        "visa_types": ["F-1", "H-4", "L-1"],
    },
}


def get_processing_times() -> list[dict[str, Any]]:
    """Return curated USCIS processing times as content items."""
    logger.info("Preparing USCIS processing times data...")
    content_items = []

    for form_number, data in PROCESSING_TIMES_DATA.items():
        lines = [
            f"USCIS Processing Times for Form {form_number}: {data['form_name']}",
            f"\nCategory: {data['category']}",
            f"\nEstimated processing times (80% of cases completed within):",
        ]

        for center, time_range in data["times"].items():
            lines.append(f"  {center}: {time_range}")

        lines.append(
            f"\nNote: Processing times are estimates and may vary. "
            f"Check USCIS.gov/processing-times for the most current data. "
            f"Premium Processing (where available) guarantees a response within 15 business days."
        )

        text = "\n".join(lines)

        content_items.append({
            "content": text,
            "metadata": {
                "source": "processing_times",
                "document_title": f"Processing Times: {form_number} - {data['form_name']}",
                "form_number": form_number,
                "visa_types": data["visa_types"],
                "section": f"pt_{form_number.lower().replace('-', '')}",
            },
        })

    logger.info(f"Prepared {len(content_items)} processing times items")
    return content_items


# --- Federal Register scraper ---

FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1/documents.json"

VISA_TYPE_KEYWORDS = {
    "H-1B": ["h-1b", "h1b", "specialty occupation"],
    "H-4": ["h-4", "h4", "h-1b dependent"],
    "L-1": ["l-1", "l1", "intracompany transfer"],
    "O-1": ["o-1", "o1", "extraordinary ability"],
    "F-1": ["f-1", "f1", "student visa", "academic student"],
    "OPT": ["opt", "optional practical training"],
    "EB-1": ["eb-1", "eb1", "first preference", "priority worker"],
    "EB-2": ["eb-2", "eb2", "second preference", "advanced degree"],
    "EB-3": ["eb-3", "eb3", "third preference", "skilled worker"],
    "Green Card": ["green card", "lawful permanent resident", "lpr", "adjustment of status"],
    "Naturalization": ["naturalization", "citizenship", "n-400"],
}


def infer_visa_types(text: str) -> list[str]:
    """Infer visa types from text content using keyword matching."""
    text_lower = text.lower()
    visa_types = []
    for visa_type, keywords in VISA_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                visa_types.append(visa_type)
                break
    return visa_types


def scrape_federal_register(months_back: int = 12) -> list[dict[str, Any]]:
    """Fetch immigration rules from the Federal Register API."""
    logger.info("Fetching Federal Register rules...")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)

    params = {
        "conditions[topics][]": "immigration",
        "conditions[type][]": "RULE",
        "conditions[publication_date][gte]": start_date.strftime("%Y-%m-%d"),
        "conditions[publication_date][lte]": end_date.strftime("%Y-%m-%d"),
        "order": "newest",
        "per_page": "50",
        "page": "1",
    }

    try:
        response = httpx.get(FEDERAL_REGISTER_API, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch Federal Register: {e}")
        return []

    rules = data.get("results", [])
    logger.info(f"Found {len(rules)} immigration rules")

    content_items = []
    for rule in rules:
        title = rule.get("title", "Untitled Rule")
        abstract = rule.get("abstract", "No summary available.")
        pub_date = rule.get("publication_date", "Unknown")
        doc_number = rule.get("document_number", "N/A")
        agencies = [a.get("name", "") for a in rule.get("agencies", []) if a.get("name")]

        # Format effective date
        effective_date = pub_date
        eff_match = re.search(
            r"effective\s+(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
            abstract, re.IGNORECASE
        )
        if eff_match:
            effective_date = eff_match.group(1)

        combined_text = f"{title} {abstract}"
        visa_types = infer_visa_types(combined_text)

        text = (
            f"Federal Register Rule: {title}\n\n"
            f"Published: {pub_date} by {', '.join(agencies) or 'Federal agencies'}\n"
            f"Effective: {effective_date}\n"
            f"Document Number: {doc_number}\n\n"
            f"Summary: {abstract}\n\n"
            f"This rule affects: {', '.join(visa_types) or 'multiple immigration categories'}\n\n"
            f"Source: Federal Register Document {doc_number}."
        )

        content_items.append({
            "content": text,
            "metadata": {
                "source": "federal_register",
                "document_title": f"Federal Register: {title}",
                "document_number": doc_number,
                "publication_date": pub_date,
                "visa_types": visa_types,
                "section": f"doc_{doc_number}_chunk_0",
            },
        })

    logger.info(f"Prepared {len(content_items)} federal register items")
    return content_items


# --- Main refresh function ---


def refresh_pinecone_vectors() -> dict[str, int]:
    """
    Refresh time-sensitive Pinecone vectors.

    Returns dict with counts per source.
    """
    # Initialize clients
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    pinecone_index_name = os.environ.get("PINECONE_INDEX_NAME", "immigration-docs")

    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY environment variable is required")

    openai_client = OpenAI(
        api_key=openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    pc = Pinecone(api_key=pinecone_api_key)
    index = pc.Index(pinecone_index_name)

    results = {}

    # 1. Visa Bulletin
    try:
        vb_items = scrape_visa_bulletin()
        if vb_items:
            chunks = [item["content"] for item in vb_items]
            metadata = [item["metadata"] for item in vb_items]
            count = upsert_chunks_sync(openai_client, index, chunks, metadata, "visa_bulletin")
            results["visa_bulletin"] = count
            logger.info(f"Visa Bulletin: {count} vectors upserted")
        else:
            results["visa_bulletin"] = 0
    except Exception as e:
        logger.error(f"Visa Bulletin refresh failed: {e}")
        results["visa_bulletin"] = -1

    # 2. Processing Times
    try:
        pt_items = get_processing_times()
        if pt_items:
            chunks = [item["content"] for item in pt_items]
            metadata = [item["metadata"] for item in pt_items]
            count = upsert_chunks_sync(openai_client, index, chunks, metadata, "processing_times")
            results["processing_times"] = count
            logger.info(f"Processing Times: {count} vectors upserted")
        else:
            results["processing_times"] = 0
    except Exception as e:
        logger.error(f"Processing Times refresh failed: {e}")
        results["processing_times"] = -1

    # 3. Federal Register
    try:
        fr_items = scrape_federal_register()
        if fr_items:
            chunks = [item["content"] for item in fr_items]
            metadata = [item["metadata"] for item in fr_items]
            count = upsert_chunks_sync(openai_client, index, chunks, metadata, "federal_register")
            results["federal_register"] = count
            logger.info(f"Federal Register: {count} vectors upserted")
        else:
            results["federal_register"] = 0
    except Exception as e:
        logger.error(f"Federal Register refresh failed: {e}")
        results["federal_register"] = -1

    return results
