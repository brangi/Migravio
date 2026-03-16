"""
Federal Register immigration rules ingestion script for Migravio RAG pipeline.

Fetches recent immigration-related final rules from the Federal Register API
(https://www.federalregister.gov/api/v1/) and ingests them into Pinecone
for AI-assisted retrieval.

The Federal Register is the official daily publication for federal rules,
proposed rules, and notices. This script focuses on final rules related to
immigration published in the last 12 months.

Usage:
    python scripts/ingest_federal_register.py [--dry-run] [--months 12]
"""

import argparse
import asyncio
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
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

# Federal Register API endpoint
FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1/documents.json"

# Visa type keywords for inferring which rules affect which visa categories
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
    "Green Card": [
        "green card",
        "lawful permanent resident",
        "lpr",
        "adjustment of status",
    ],
    "Naturalization": ["naturalization", "citizenship", "n-400"],
}


def infer_visa_types(text: str) -> list[str]:
    """
    Infer visa types from text content using keyword matching.

    Args:
        text: Text to analyze (title + abstract)

    Returns:
        List of visa type tags (e.g., ["H-1B", "F-1"])
    """
    text_lower = text.lower()
    visa_types = []

    for visa_type, keywords in VISA_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                visa_types.append(visa_type)
                break

    return visa_types


async def fetch_federal_register_rules(
    client: httpx.AsyncClient, months_back: int = 12, per_page: int = 50
) -> list[dict[str, Any]]:
    """
    Fetch immigration rules from the Federal Register API.

    Args:
        client: httpx AsyncClient instance
        months_back: Number of months to look back for rules
        per_page: Results per page (max 100)

    Returns:
        List of rule documents from the API
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months_back * 30)

    # Format dates for API (YYYY-MM-DD)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    logger.info(
        f"Fetching Federal Register rules from {start_date_str} to {end_date_str}"
    )

    # API parameters
    params = {
        "conditions[topics][]": "immigration",
        "conditions[type][]": "RULE",
        "conditions[publication_date][gte]": start_date_str,
        "conditions[publication_date][lte]": end_date_str,
        "order": "newest",
        "per_page": str(per_page),
        "page": "1",
    }

    try:
        response = await client.get(FEDERAL_REGISTER_API, params=params, timeout=30.0)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        count = data.get("count", 0)

        logger.info(f"Found {count} immigration rules in Federal Register")
        return results

    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch Federal Register data: {e}")
        return []


def extract_effective_date(abstract: str, publication_date: str) -> str:
    """
    Extract effective date from rule abstract.

    Args:
        abstract: Rule abstract text
        publication_date: Publication date as fallback

    Returns:
        Effective date string
    """
    # Try to find "effective [date]" pattern
    effective_pattern = re.compile(
        r"effective\s+(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", re.IGNORECASE
    )
    match = effective_pattern.search(abstract)

    if match:
        return match.group(1)

    # Try to find "effective immediately" or similar
    if re.search(r"effective\s+immediately", abstract, re.IGNORECASE):
        return f"{publication_date} (immediately)"

    # Default: assume 30 days after publication
    try:
        pub_date = datetime.strptime(publication_date, "%Y-%m-%d")
        effective_date = pub_date + timedelta(days=30)
        return f"{effective_date.strftime('%B %d, %Y')} (estimated)"
    except ValueError:
        return "See rule for details"


def format_rule_text(rule: dict[str, Any]) -> str:
    """
    Format Federal Register rule into readable text.

    Args:
        rule: Rule document from API

    Returns:
        Formatted text suitable for RAG retrieval
    """
    title = rule.get("title", "Untitled Rule")
    abstract = rule.get("abstract", "No summary available.")
    publication_date = rule.get("publication_date", "Unknown date")
    document_number = rule.get("document_number", "N/A")
    agencies = rule.get("agencies", [])

    # Format publication date
    try:
        pub_date = datetime.strptime(publication_date, "%Y-%m-%d")
        pub_date_formatted = pub_date.strftime("%B %d, %Y")
    except ValueError:
        pub_date_formatted = publication_date

    # Extract effective date
    effective_date = extract_effective_date(abstract, publication_date)

    # Format agencies
    agency_names = [agency.get("name", "") for agency in agencies if agency.get("name")]
    agencies_str = ", ".join(agency_names) if agency_names else "Federal agencies"

    # Determine visa types affected
    combined_text = f"{title} {abstract}"
    visa_types = infer_visa_types(combined_text)
    visa_types_str = (
        ", ".join(visa_types) if visa_types else "multiple immigration categories"
    )

    # Build formatted text
    lines = [
        f"Federal Register Rule: {title}",
        "",
        f"Published: {pub_date_formatted} by {agencies_str}",
        f"Effective: {effective_date}",
        f"Document Number: {document_number}",
        "",
        f"Summary: {abstract}",
        "",
        f"This rule affects: {visa_types_str}",
        "",
        f"Source: Federal Register Document {document_number}. For full text, visit federalregister.gov",
    ]

    return "\n".join(lines)


async def scrape_federal_register(
    client: httpx.AsyncClient, months_back: int = 12
) -> list[dict[str, Any]]:
    """
    Scrape Federal Register rules and prepare for ingestion.

    Args:
        client: httpx AsyncClient instance
        months_back: Number of months to look back

    Returns:
        List of dicts containing rule content and metadata
    """
    # Fetch rules from API
    rules = await fetch_federal_register_rules(client, months_back)

    if not rules:
        logger.warning("No Federal Register rules retrieved")
        return []

    scraped_content = []

    for rule in rules:
        title = rule.get("title", "Untitled Rule")
        document_number = rule.get("document_number", "N/A")

        logger.info(f"  Processing rule: {title[:60]}...")

        # Format text content
        text_content = format_rule_text(rule)

        # Infer visa types
        combined_text = f"{title} {rule.get('abstract', '')}"
        visa_types = infer_visa_types(combined_text)

        # Extract publication date
        publication_date = rule.get("publication_date", "")

        scraped_content.append(
            {
                "content": text_content,
                "metadata": {
                    "source": "federal_register",
                    "document_title": f"Federal Register: {title}",
                    "document_number": document_number,
                    "publication_date": publication_date,
                    "visa_types": visa_types,
                    "agencies": [
                        agency.get("name", "")
                        for agency in rule.get("agencies", [])
                        if agency.get("name")
                    ],
                },
            }
        )

    return scraped_content


async def ingest_federal_register(dry_run: bool = False, months_back: int = 12):
    """
    Main ingestion function for Federal Register rules.

    Args:
        dry_run: If True, skip actual API calls
        months_back: Number of months to look back for rules
    """
    logger.info("Starting Federal Register ingestion")
    logger.info(f"Dry run: {dry_run}")
    logger.info(f"Looking back {months_back} months")

    # Initialize clients
    clients = await setup_clients()

    # Create HTTP client
    async with httpx.AsyncClient() as http_client:
        # Scrape Federal Register rules
        scraped_content = await scrape_federal_register(http_client, months_back)

        if not scraped_content:
            logger.warning("No Federal Register content retrieved")
            return

        # Prepare chunks and metadata
        all_chunks = []
        all_metadata = []

        for item in scraped_content:
            content = item["content"]
            metadata_base = item["metadata"]

            # Chunk text
            chunks = chunk_text(content, chunk_size=512, overlap=50)
            logger.info(
                f"  Created {len(chunks)} chunks from {metadata_base['document_title'][:60]}..."
            )

            # Create metadata for each chunk
            for chunk_idx, chunk in enumerate(chunks):
                metadata = metadata_base.copy()
                metadata["chunk_index"] = chunk_idx
                # Include document_number and chunk_index in section for unique vector IDs
                section = f"doc_{metadata_base['document_number']}_chunk_{chunk_idx}"
                metadata["section"] = section

                all_chunks.append(chunk)
                all_metadata.append(metadata)

        # Upsert to Pinecone
        if all_chunks:
            logger.info(f"Upserting {len(all_chunks)} chunks to Pinecone")

            vectors_upserted = await upsert_to_pinecone(
                clients.index,
                all_chunks,
                all_metadata,
                source="federal_register",
                dry_run=dry_run,
            )

            logger.info(f"\n✓ Ingestion complete: {vectors_upserted} vectors upserted")
        else:
            logger.warning("No chunks to ingest")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest Federal Register immigration rules into Pinecone for RAG"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without calling APIs",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="Number of months to look back for rules (default: 12)",
    )

    args = parser.parse_args()

    asyncio.run(
        ingest_federal_register(
            dry_run=args.dry_run,
            months_back=args.months,
        )
    )


if __name__ == "__main__":
    main()
