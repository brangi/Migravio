"""
DOS Visa Bulletin ingestion script for Migravio RAG pipeline.

Scrapes the Department of State Visa Bulletin
(https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html)
and ingests it into Pinecone for AI-assisted retrieval.

The Visa Bulletin contains monthly priority date information for employment-based
and family-based immigration categories. Each bulletin includes:
- Final Action Dates (when applicants can be processed)
- Dates for Filing (when applicants can submit applications)

Each table tracks priority dates for different countries/regions:
All Countries, China, India, Mexico, Philippines

Usage:
    python scripts/ingest_visa_bulletin.py [--dry-run]
"""

import argparse
import asyncio
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Add scripts directory to path for shared module import
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared import chunk_text, setup_clients, upsert_to_pinecone

# Load environment variables from ai-service directory
ENV_PATH = SCRIPT_DIR.parent / "apps" / "ai-service" / ".env"
load_dotenv(ENV_PATH)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Base URL for DOS Visa Bulletin
VISA_BULLETIN_BASE_URL = "https://travel.state.gov"
VISA_BULLETIN_MAIN_PAGE = (
    "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html"
)

# Employment-based categories
EB_CATEGORIES = ["EB-1", "EB-2", "EB-3", "EB-4", "EB-5"]

# Family-based categories
FB_CATEGORIES = ["F1", "F2A", "F2B", "F3", "F4"]

# Country/region columns
COUNTRIES = ["All Countries", "China", "India", "Mexico", "Philippines"]

# Visa type mappings for metadata
VISA_TYPE_MAPPING = {
    "EB-1": ["EB-1", "Green Card"],
    "EB-2": ["EB-2", "Green Card"],
    "EB-3": ["EB-3", "Green Card"],
    "EB-4": ["Green Card"],
    "EB-5": ["Green Card"],
    "F1": ["Green Card"],
    "F2A": ["Green Card"],
    "F2B": ["Green Card"],
    "F3": ["Green Card"],
    "F4": ["Green Card"],
}


async def fetch_page(url: str, client: httpx.AsyncClient) -> str | None:
    """
    Fetch HTML content from a URL.

    Args:
        url: URL to fetch
        client: httpx AsyncClient instance

    Returns:
        HTML content as string, or None if request fails
    """
    try:
        logger.info(f"Fetching: {url}")
        response = await client.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def extract_current_bulletin_link(html: str) -> tuple[str | None, str | None]:
    """
    Extract the link to the current month's visa bulletin from the main page.

    Args:
        html: HTML content of main visa bulletin page

    Returns:
        Tuple of (bulletin_url, bulletin_title) or (None, None) if not found
    """
    soup = BeautifulSoup(html, "html.parser")

    # Look for links that point to current bulletin
    # Common patterns: "visa-bulletin/2026/visa-bulletin-for-march-2026.html"
    # or text containing "current" or the current year
    current_year = datetime.now().year

    # Strategy 1: Find links with current year in URL
    links = soup.find_all("a", href=re.compile(rf"/visa-bulletin/{current_year}/"))

    if links:
        # Get the first link (usually most recent)
        link = links[0]
        href = link.get("href", "")
        title = link.get_text(strip=True)

        # Normalize URL
        full_url = f"{VISA_BULLETIN_BASE_URL}{href}" if href.startswith("/") else href

        logger.info(f"Found current bulletin: {title}")
        return full_url, title

    # Strategy 2: Look for text containing "current" or recent month names
    month_names = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ]
    current_month = datetime.now().strftime("%B").lower()

    for link in soup.find_all("a", href=re.compile(r"/visa-bulletin/")):
        text = link.get_text(strip=True).lower()
        href = link.get("href", "")

        if current_month in text and str(current_year) in text:
            full_url = (
                f"{VISA_BULLETIN_BASE_URL}{href}" if href.startswith("/") else href
            )
            title = link.get_text(strip=True)
            logger.info(f"Found current bulletin (by month): {title}")
            return full_url, title

    logger.warning("Could not find current bulletin link on main page")
    return None, None


def parse_bulletin_metadata(html: str, title: str) -> dict[str, Any]:
    """
    Extract bulletin month and year from HTML and title.

    Args:
        html: HTML content of bulletin page
        title: Bulletin title from link

    Returns:
        Dict with 'month', 'year', 'display_name' keys
    """
    # Try to extract from title first
    # Example: "Visa Bulletin For March 2026"
    match = re.search(r"(\w+)\s+(\d{4})", title, re.IGNORECASE)

    if match:
        month = match.group(1).capitalize()
        year = match.group(2)
        return {
            "month": month,
            "year": year,
            "display_name": f"{month} {year}",
        }

    # Fallback: use current date
    now = datetime.now()
    return {
        "month": now.strftime("%B"),
        "year": str(now.year),
        "display_name": f"{now.strftime('%B')} {now.year}",
    }


def parse_priority_date_table(
    table: Any, table_type: str, category_prefix: str
) -> list[dict[str, Any]]:
    """
    Parse a priority date table (employment-based or family-based).

    Args:
        table: BeautifulSoup table element
        table_type: "employment" or "family"
        category_prefix: "EB" or "F"

    Returns:
        List of dicts with parsed priority date data
    """
    results = []

    try:
        rows = table.find_all("tr")

        # Skip header row(s)
        data_rows = [r for r in rows if r.find("td")]

        for row in data_rows:
            cells = row.find_all("td")

            if len(cells) < 2:
                continue

            # First cell is category (e.g., "1st", "2nd", "3rd" or "F1", "F2A")
            category_cell = cells[0].get_text(strip=True)

            # Map row label to category code
            if table_type == "employment":
                # Map "1st" → "EB-1", "2nd" → "EB-2", etc.
                category_map = {
                    "1st": "EB-1",
                    "2nd": "EB-2",
                    "3rd": "EB-3",
                    "4th": "EB-4",
                    "5th": "EB-5",
                    "C5": "EB-5",
                    "T5": "EB-5",
                    "I5": "EB-5",
                    "R5": "EB-5",
                }
                category = category_map.get(category_cell, category_cell)
            else:
                # Family-based: usually already labeled F1, F2A, etc.
                category = category_cell.upper()

            # Remaining cells are country-specific dates
            # Typical order: All Countries, China, India, Mexico, Philippines
            country_data = {}

            for i, country in enumerate(COUNTRIES):
                cell_idx = i + 1  # Skip first cell (category)
                if cell_idx < len(cells):
                    date_text = cells[cell_idx].get_text(strip=True)
                    country_data[country] = date_text

            results.append({"category": category, "dates": country_data})

    except Exception as e:
        logger.error(f"Error parsing table: {e}")

    return results


def extract_priority_dates(html: str, bulletin_meta: dict[str, Any]) -> dict[str, Any]:
    """
    Extract all priority date tables from the visa bulletin page.

    Args:
        html: HTML content of bulletin page
        bulletin_meta: Metadata dict with month/year info

    Returns:
        Dict with 'final_action' and 'dates_for_filing' keys, each containing
        'employment' and 'family' table data
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove navigation, headers, footers
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    # Find all tables
    tables = soup.find_all("table")

    logger.info(f"Found {len(tables)} tables in bulletin")

    result = {
        "final_action": {"employment": [], "family": []},
        "dates_for_filing": {"employment": [], "family": []},
    }

    # Strategy: Look for tables near headings containing keywords
    # "Final Action Dates" and "Dates for Filing"
    for table in tables:
        # Get preceding heading context
        preceding_text = ""
        prev_elem = table.find_previous(["h1", "h2", "h3", "h4", "p"])

        if prev_elem:
            # Get up to 3 preceding elements for context
            context_elements = []
            current = prev_elem
            for _ in range(3):
                if current:
                    context_elements.append(current.get_text(strip=True))
                    current = current.find_previous(["h1", "h2", "h3", "h4", "p"])
                else:
                    break

            preceding_text = " ".join(context_elements).lower()

        # Determine table type
        is_final_action = (
            "final action" in preceding_text or "application final" in preceding_text
        )
        is_dates_for_filing = "dates for filing" in preceding_text or "filing" in preceding_text
        is_employment = (
            "employment" in preceding_text or "employment-based" in preceding_text
        )
        is_family = "family" in preceding_text or "family-sponsored" in preceding_text

        # Parse table based on type
        if is_final_action and is_employment:
            logger.info("Parsing: Final Action Dates - Employment-Based")
            parsed = parse_priority_date_table(table, "employment", "EB")
            result["final_action"]["employment"] = parsed

        elif is_final_action and is_family:
            logger.info("Parsing: Final Action Dates - Family-Based")
            parsed = parse_priority_date_table(table, "family", "F")
            result["final_action"]["family"] = parsed

        elif is_dates_for_filing and is_employment:
            logger.info("Parsing: Dates for Filing - Employment-Based")
            parsed = parse_priority_date_table(table, "employment", "EB")
            result["dates_for_filing"]["employment"] = parsed

        elif is_dates_for_filing and is_family:
            logger.info("Parsing: Dates for Filing - Family-Based")
            parsed = parse_priority_date_table(table, "family", "F")
            result["dates_for_filing"]["family"] = parsed

    return result


def format_priority_date_chunk(
    category: str,
    dates: dict[str, str],
    table_type: str,
    bulletin_meta: dict[str, Any],
) -> str:
    """
    Format priority date data into a readable text chunk.

    Args:
        category: Category code (e.g., "EB-2", "F2A")
        dates: Dict mapping country to date string
        table_type: "Final Action Dates" or "Dates for Filing"
        bulletin_meta: Bulletin metadata with month/year

    Returns:
        Formatted text chunk
    """
    lines = [
        f"Visa Bulletin for {bulletin_meta['display_name']}",
        f"{table_type} - {category}",
        "",
    ]

    for country, date in dates.items():
        lines.append(f"  {country}: {date}")

    return "\n".join(lines)


def create_explanatory_chunks(bulletin_meta: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Create explanatory context chunks about the visa bulletin.

    Args:
        bulletin_meta: Bulletin metadata with month/year

    Returns:
        List of dicts with content and metadata for explanatory chunks
    """
    display_name = bulletin_meta["display_name"]

    chunks = [
        {
            "content": f"""What is the Visa Bulletin? ({display_name})

The Visa Bulletin is published monthly by the U.S. Department of State and shows when immigrant visa applicants can take the next step in their green card process. It contains priority dates for employment-based (EB) and family-based (FB) immigration categories.

A priority date is the date when your immigration petition (like I-140 or I-130) was filed. When your priority date becomes "current" according to the Visa Bulletin, you can move forward with your green card application.

The bulletin is essential for anyone waiting for a green card through employment or family sponsorship.""",
            "metadata": {
                "source": "visa_bulletin",
                "document_title": f"Visa Bulletin Explanation - {display_name}",
                "section": "explanation_what_is",
                "visa_types": ["Green Card"],
                "bulletin_month": bulletin_meta["month"],
                "bulletin_year": bulletin_meta["year"],
            },
        },
        {
            "content": f"""How to Read Priority Dates ({display_name})

The Visa Bulletin contains two types of dates:

1. Final Action Dates (previously "Application Final Action Dates")
   - These dates determine when you can be approved for your green card
   - If your priority date is earlier than the date shown, visa numbers are available for you

2. Dates for Filing (previously "Filing Dates")
   - These dates determine when you can submit your adjustment of status application (Form I-485)
   - USCIS announces each month whether they will accept applications based on Filing Dates or Final Action Dates

The bulletin shows different dates for different countries because of per-country visa limits. India and China typically have longer waits due to high demand.""",
            "metadata": {
                "source": "visa_bulletin",
                "document_title": f"Visa Bulletin Explanation - {display_name}",
                "section": "explanation_how_to_read",
                "visa_types": ["Green Card"],
                "bulletin_month": bulletin_meta["month"],
                "bulletin_year": bulletin_meta["year"],
            },
        },
        {
            "content": f"""Understanding "Current" and Per-Country Limits ({display_name})

When a category shows "C" or "Current":
- This means all priority dates are current
- Anyone with an approved petition in this category can proceed immediately
- There is no backlog for this category and country

Why India and China have longer waits:
- U.S. immigration law limits visas to 7% per country per year
- India and China have very high demand for employment-based green cards
- This creates multi-year backlogs, especially in EB-2 and EB-3 categories

"All Chargeability Areas Except Those Listed":
- This column applies to most countries
- If your birth country is not listed (China, India, Mexico, Philippines), use this column""",
            "metadata": {
                "source": "visa_bulletin",
                "document_title": f"Visa Bulletin Explanation - {display_name}",
                "section": "explanation_current_and_limits",
                "visa_types": ["Green Card"],
                "bulletin_month": bulletin_meta["month"],
                "bulletin_year": bulletin_meta["year"],
            },
        },
        {
            "content": f"""Employment-Based Categories ({display_name})

EB-1: Priority Workers
- EB-1A: Extraordinary ability in sciences, arts, education, business, or athletics
- EB-1B: Outstanding professors and researchers
- EB-1C: Multinational executives and managers

EB-2: Professionals with Advanced Degrees or Exceptional Ability
- Requires master's degree or bachelor's + 5 years experience
- Can include National Interest Waiver (NIW) cases

EB-3: Skilled Workers, Professionals, and Other Workers
- Requires bachelor's degree or at least 2 years work experience
- "Other Workers" subcategory for unskilled positions (often has longer wait)

EB-4: Special Immigrants (religious workers, certain international organization employees)

EB-5: Immigrant Investors ($800,000 or $1.05 million investment)""",
            "metadata": {
                "source": "visa_bulletin",
                "document_title": f"Visa Bulletin Explanation - {display_name}",
                "section": "explanation_employment_categories",
                "visa_types": ["Green Card", "EB-1", "EB-2", "EB-3"],
                "bulletin_month": bulletin_meta["month"],
                "bulletin_year": bulletin_meta["year"],
            },
        },
        {
            "content": f"""Family-Based Categories ({display_name})

F1: Unmarried Sons and Daughters of U.S. Citizens
- Includes adult children (21 years or older)

F2A: Spouses and Children (under 21) of Lawful Permanent Residents
- Often has shorter wait times
- Sometimes goes "Current"

F2B: Unmarried Sons and Daughters (21 or older) of Lawful Permanent Residents

F3: Married Sons and Daughters of U.S. Citizens

F4: Brothers and Sisters of Adult U.S. Citizens
- Longest wait times, often 10+ years

Note: Immediate relatives of U.S. citizens (spouses, parents, children under 21) are NOT subject to visa bulletin wait times and can apply immediately.""",
            "metadata": {
                "source": "visa_bulletin",
                "document_title": f"Visa Bulletin Explanation - {display_name}",
                "section": "explanation_family_categories",
                "visa_types": ["Green Card"],
                "bulletin_month": bulletin_meta["month"],
                "bulletin_year": bulletin_meta["year"],
            },
        },
    ]

    return chunks


async def scrape_visa_bulletin(
    client: httpx.AsyncClient, rate_limit_delay: float = 2.0
) -> list[dict[str, Any]]:
    """
    Scrape the DOS Visa Bulletin and prepare content for ingestion.

    Args:
        client: httpx AsyncClient instance
        rate_limit_delay: Delay in seconds between requests

    Returns:
        List of dicts containing content and metadata for ingestion
    """
    logger.info("Starting Visa Bulletin scrape")

    # Fetch main visa bulletin page
    main_html = await fetch_page(VISA_BULLETIN_MAIN_PAGE, client)
    if not main_html:
        logger.error("Failed to fetch main visa bulletin page")
        return []

    # Extract link to current bulletin
    bulletin_url, bulletin_title = extract_current_bulletin_link(main_html)
    if not bulletin_url:
        logger.error("Could not find current bulletin link")
        return []

    # Rate limiting
    await asyncio.sleep(rate_limit_delay)

    # Fetch current bulletin page
    bulletin_html = await fetch_page(bulletin_url, client)
    if not bulletin_html:
        logger.error("Failed to fetch current bulletin page")
        return []

    # Extract metadata (month/year)
    bulletin_meta = parse_bulletin_metadata(bulletin_html, bulletin_title)
    logger.info(f"Processing bulletin: {bulletin_meta['display_name']}")

    # Parse priority date tables
    priority_data = extract_priority_dates(bulletin_html, bulletin_meta)

    # Prepare content chunks
    scraped_content = []

    # Add explanatory chunks
    explanatory_chunks = create_explanatory_chunks(bulletin_meta)
    scraped_content.extend(explanatory_chunks)

    # Format Final Action Dates
    for category_data in priority_data["final_action"]["employment"]:
        content = format_priority_date_chunk(
            category_data["category"],
            category_data["dates"],
            "Final Action Dates - Employment-Based",
            bulletin_meta,
        )
        visa_types = VISA_TYPE_MAPPING.get(
            category_data["category"], ["Green Card"]
        )

        scraped_content.append(
            {
                "content": content,
                "metadata": {
                    "source": "visa_bulletin",
                    "document_title": f"Visa Bulletin {bulletin_meta['display_name']} - Final Action {category_data['category']}",
                    "section": f"final_action_employment_{category_data['category'].lower().replace('-', '')}",
                    "visa_types": visa_types,
                    "bulletin_month": bulletin_meta["month"],
                    "bulletin_year": bulletin_meta["year"],
                    "category": category_data["category"],
                    "table_type": "final_action",
                },
            }
        )

    for category_data in priority_data["final_action"]["family"]:
        content = format_priority_date_chunk(
            category_data["category"],
            category_data["dates"],
            "Final Action Dates - Family-Based",
            bulletin_meta,
        )

        scraped_content.append(
            {
                "content": content,
                "metadata": {
                    "source": "visa_bulletin",
                    "document_title": f"Visa Bulletin {bulletin_meta['display_name']} - Final Action {category_data['category']}",
                    "section": f"final_action_family_{category_data['category'].lower()}",
                    "visa_types": ["Green Card"],
                    "bulletin_month": bulletin_meta["month"],
                    "bulletin_year": bulletin_meta["year"],
                    "category": category_data["category"],
                    "table_type": "final_action",
                },
            }
        )

    # Format Dates for Filing
    for category_data in priority_data["dates_for_filing"]["employment"]:
        content = format_priority_date_chunk(
            category_data["category"],
            category_data["dates"],
            "Dates for Filing - Employment-Based",
            bulletin_meta,
        )
        visa_types = VISA_TYPE_MAPPING.get(
            category_data["category"], ["Green Card"]
        )

        scraped_content.append(
            {
                "content": content,
                "metadata": {
                    "source": "visa_bulletin",
                    "document_title": f"Visa Bulletin {bulletin_meta['display_name']} - Filing Dates {category_data['category']}",
                    "section": f"filing_dates_employment_{category_data['category'].lower().replace('-', '')}",
                    "visa_types": visa_types,
                    "bulletin_month": bulletin_meta["month"],
                    "bulletin_year": bulletin_meta["year"],
                    "category": category_data["category"],
                    "table_type": "dates_for_filing",
                },
            }
        )

    for category_data in priority_data["dates_for_filing"]["family"]:
        content = format_priority_date_chunk(
            category_data["category"],
            category_data["dates"],
            "Dates for Filing - Family-Based",
            bulletin_meta,
        )

        scraped_content.append(
            {
                "content": content,
                "metadata": {
                    "source": "visa_bulletin",
                    "document_title": f"Visa Bulletin {bulletin_meta['display_name']} - Filing Dates {category_data['category']}",
                    "section": f"filing_dates_family_{category_data['category'].lower()}",
                    "visa_types": ["Green Card"],
                    "bulletin_month": bulletin_meta["month"],
                    "bulletin_year": bulletin_meta["year"],
                    "category": category_data["category"],
                    "table_type": "dates_for_filing",
                },
            }
        )

    logger.info(f"Created {len(scraped_content)} content chunks from visa bulletin")
    return scraped_content


async def ingest_visa_bulletin(dry_run: bool = False, rate_limit_delay: float = 2.0):
    """
    Main ingestion function for DOS Visa Bulletin.

    Args:
        dry_run: If True, skip actual API calls
        rate_limit_delay: Delay in seconds between requests
    """
    logger.info("Starting DOS Visa Bulletin ingestion")
    logger.info(f"Dry run: {dry_run}")

    # Initialize clients
    clients = await setup_clients()

    # Scrape visa bulletin
    total_vectors = 0

    async with httpx.AsyncClient() as http_client:
        scraped_content = await scrape_visa_bulletin(http_client, rate_limit_delay)

        if not scraped_content:
            logger.warning("No content scraped from visa bulletin")
            return

        # Chunk and prepare for ingestion
        chunks = []
        metadata = []

        for item in scraped_content:
            content = item["content"]
            metadata_base = item["metadata"]

            # For visa bulletin, chunks are already small enough - just use as-is
            # But we'll still apply chunk_text to ensure consistency
            text_chunks = chunk_text(content, chunk_size=512, overlap=50)

            if len(text_chunks) == 1:
                # Single chunk - use original content
                metadata_item = metadata_base.copy()
                chunks.append(content)
                metadata.append(metadata_item)
            else:
                # Multiple chunks - add chunk index
                for chunk_idx, chunk in enumerate(text_chunks):
                    metadata_item = metadata_base.copy()
                    metadata_item["chunk_index"] = chunk_idx
                    metadata_item["section"] = f"{metadata_base['section']}_chunk_{chunk_idx}"

                    chunks.append(chunk)
                    metadata.append(metadata_item)

        logger.info(f"Prepared {len(chunks)} total chunks for ingestion")

        # Upsert to Pinecone
        if chunks:
            vectors_upserted = await upsert_to_pinecone(
                clients.index,
                chunks,
                metadata,
                source="visa_bulletin",
                dry_run=dry_run,
            )

            total_vectors += vectors_upserted
            logger.info(f"✓ Visa Bulletin: {vectors_upserted} vectors upserted")

    if total_vectors > 0:
        logger.info(f"\n✓ Ingestion complete: {total_vectors} total vectors upserted")
    else:
        logger.warning("No chunks to ingest")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest DOS Visa Bulletin into Pinecone for RAG"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without calling APIs",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=2.0,
        help="Delay in seconds between requests (default: 2.0)",
    )

    args = parser.parse_args()

    asyncio.run(
        ingest_visa_bulletin(
            dry_run=args.dry_run,
            rate_limit_delay=args.rate_limit,
        )
    )


if __name__ == "__main__":
    main()
