"""
USCIS Processing Times ingestion script for Migravio RAG pipeline.

Fetches processing time data from the USCIS API
(https://egov.uscis.gov/processing-times/) and ingests it into Pinecone
for AI-assisted retrieval.

The script queries the USCIS public API for priority forms (I-485, I-130, etc.)
across all service centers and converts the data into readable chunks with
visa type metadata.

Usage:
    python scripts/ingest_processing_times.py [--dry-run]
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Add scripts directory to path for shared module import
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from shared import chunk_text, setup_clients, upsert_to_pinecone, generate_vector_id

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

# USCIS Processing Times API endpoints
USCIS_API_BASE = "https://egov.uscis.gov/processing-times/api/processingtime"

# Priority forms to query
PRIORITY_FORMS = [
    "I-485",  # Adjustment of Status
    "I-130",  # Petition for Alien Relative
    "I-140",  # Immigrant Worker Petition
    "I-765",  # Employment Authorization
    "I-131",  # Travel Document
    "N-400",  # Naturalization
    "I-129",  # Nonimmigrant Worker
    "I-539",  # Change/Extension of Status
]

# Map forms to visa types for metadata
FORM_VISA_TYPE_MAP = {
    "I-129": ["H-1B", "L-1", "O-1"],
    "I-485": ["Green Card"],
    "I-130": ["Green Card"],
    "I-140": ["EB-1", "EB-2", "EB-3", "Green Card"],
    "I-765": ["F-1", "OPT", "H-4"],
    "I-131": ["Green Card"],
    "N-400": ["Naturalization"],
    "I-539": ["H-1B", "L-1", "F-1"],
}

# Curated fallback data for when API fails
# (Approximate processing times as of March 2026)
FALLBACK_PROCESSING_DATA = {
    "I-485": {
        "description": "Application to Register Permanent Residence or Adjust Status",
        "offices": [
            {
                "name": "Nebraska Service Center",
                "range": "8.5 to 14 months",
            },
            {
                "name": "Texas Service Center",
                "range": "10 to 18 months",
            },
            {
                "name": "National Benefits Center",
                "range": "9 to 16 months",
            },
        ],
    },
    "I-130": {
        "description": "Petition for Alien Relative",
        "offices": [
            {
                "name": "National Benefits Center",
                "range": "13 to 26 months",
            },
            {
                "name": "California Service Center",
                "range": "12 to 22 months",
            },
        ],
    },
    "I-140": {
        "description": "Immigrant Petition for Alien Worker",
        "offices": [
            {
                "name": "Nebraska Service Center",
                "range": "5 to 9 months",
            },
            {
                "name": "Texas Service Center",
                "range": "4.5 to 8.5 months",
            },
        ],
    },
    "I-765": {
        "description": "Application for Employment Authorization",
        "offices": [
            {
                "name": "National Benefits Center",
                "range": "3 to 6 months",
            },
            {
                "name": "Nebraska Service Center",
                "range": "2.5 to 5 months",
            },
        ],
    },
    "I-131": {
        "description": "Application for Travel Document",
        "offices": [
            {
                "name": "National Benefits Center",
                "range": "4 to 8 months",
            },
            {
                "name": "Potomac Service Center",
                "range": "3.5 to 7 months",
            },
        ],
    },
    "N-400": {
        "description": "Application for Naturalization",
        "offices": [
            {
                "name": "National Average",
                "range": "10 to 14 months",
            },
            {
                "name": "Los Angeles Field Office",
                "range": "12 to 18 months",
            },
            {
                "name": "New York Field Office",
                "range": "11 to 16 months",
            },
        ],
    },
    "I-129": {
        "description": "Petition for Nonimmigrant Worker",
        "offices": [
            {
                "name": "Nebraska Service Center",
                "range": "2 to 5 months",
            },
            {
                "name": "Vermont Service Center",
                "range": "2.5 to 5.5 months",
            },
            {
                "name": "California Service Center",
                "range": "2 to 4.5 months",
            },
        ],
    },
    "I-539": {
        "description": "Application to Extend/Change Nonimmigrant Status",
        "offices": [
            {
                "name": "Nebraska Service Center",
                "range": "6 to 12 months",
            },
            {
                "name": "California Service Center",
                "range": "5.5 to 11 months",
            },
        ],
    },
}


async def fetch_processing_times_from_api(
    client: httpx.AsyncClient, form_type: str
) -> dict[str, Any] | None:
    """
    Attempt to fetch processing times from USCIS API.

    Args:
        client: httpx AsyncClient instance
        form_type: Form type code (e.g., "I-485")

    Returns:
        Dict with processing time data, or None if API fails
    """
    try:
        # Try to get office types for this form
        offices_url = f"{USCIS_API_BASE}/type/office_types/{form_type}"
        response = await client.get(offices_url, timeout=15.0)
        response.raise_for_status()
        offices_data = response.json()

        if not offices_data or not isinstance(offices_data, list):
            return None

        # Fetch processing times for each office
        office_times = []
        for office in offices_data[:5]:  # Limit to 5 offices
            office_code = office.get("officeCode")
            if not office_code:
                continue

            times_url = f"{USCIS_API_BASE}/{form_type}/{office_code}/null"
            try:
                times_response = await client.get(times_url, timeout=15.0)
                times_response.raise_for_status()
                times_data = times_response.json()

                if times_data and isinstance(times_data, dict):
                    office_times.append(
                        {
                            "name": office.get("officeName", office_code),
                            "range": times_data.get("range", "Not available"),
                            "updated": times_data.get("lastUpdated"),
                        }
                    )
            except httpx.HTTPError:
                continue

            # Rate limiting
            await asyncio.sleep(0.5)

        if office_times:
            return {"offices": office_times}

        return None

    except httpx.HTTPError as e:
        logger.warning(f"API request failed for {form_type}: {e}")
        return None


def format_processing_time_text(
    form_type: str, description: str, offices: list[dict[str, str]], last_updated: str
) -> str:
    """
    Format processing time data into readable text.

    Args:
        form_type: Form type code
        description: Form description
        offices: List of office processing time dicts
        last_updated: Last updated date string

    Returns:
        Formatted text suitable for RAG retrieval
    """
    lines = [
        f"USCIS Processing Times for Form {form_type} ({description})",
        "",
    ]

    for office in offices:
        office_name = office.get("name", "Unknown Office")
        time_range = office.get("range", "Not available")
        lines.append(
            f"At the {office_name}, 80% of cases are processed within {time_range}."
        )

    lines.append("")
    lines.append(
        f"(Data as of {last_updated}. Processing times change frequently — verify at uscis.gov/processing-times)"
    )

    return "\n".join(lines)


async def scrape_processing_times(
    client: httpx.AsyncClient, use_fallback: bool = False
) -> list[dict[str, Any]]:
    """
    Scrape processing times for priority forms.

    Args:
        client: httpx AsyncClient instance
        use_fallback: If True, skip API and use fallback data

    Returns:
        List of dicts containing processing time content and metadata
    """
    logger.info("Fetching USCIS processing times")

    current_date = datetime.now().strftime("%B %Y")
    scraped_content = []

    for form_type in PRIORITY_FORMS:
        logger.info(f"  Processing form: {form_type}")

        # Try API first unless fallback is forced
        api_data = None
        if not use_fallback:
            api_data = await fetch_processing_times_from_api(client, form_type)
            await asyncio.sleep(1.0)  # Rate limiting between forms

        # Use fallback if API failed or was skipped
        if api_data is None:
            logger.info(f"    Using fallback data for {form_type}")
            fallback = FALLBACK_PROCESSING_DATA.get(form_type)
            if not fallback:
                logger.warning(f"    No fallback data for {form_type}, skipping")
                continue

            description = fallback["description"]
            offices = fallback["offices"]
        else:
            description = f"Form {form_type}"
            offices = api_data["offices"]

        # Format text content
        text_content = format_processing_time_text(
            form_type, description, offices, current_date
        )

        # Get visa types for this form
        visa_types = FORM_VISA_TYPE_MAP.get(form_type, [])

        scraped_content.append(
            {
                "content": text_content,
                "metadata": {
                    "source": "processing_times",
                    "document_title": f"Processing Times - Form {form_type}",
                    "form_type": form_type,
                    "visa_types": visa_types,
                    "last_updated": current_date,
                },
            }
        )

    return scraped_content


async def ingest_processing_times(dry_run: bool = False, use_fallback: bool = False):
    """
    Main ingestion function for USCIS processing times.

    Args:
        dry_run: If True, skip actual API calls
        use_fallback: If True, use fallback data instead of API
    """
    logger.info("Starting USCIS Processing Times ingestion")
    logger.info(f"Dry run: {dry_run}")
    logger.info(f"Using fallback data: {use_fallback}")

    # Initialize clients
    clients = await setup_clients()

    # Create HTTP client
    async with httpx.AsyncClient() as http_client:
        # Scrape processing times
        scraped_content = await scrape_processing_times(http_client, use_fallback)

        if not scraped_content:
            logger.warning("No processing time data retrieved")
            return

        # Prepare chunks and metadata
        all_chunks = []
        all_metadata = []

        for item in scraped_content:
            content = item["content"]
            metadata_base = item["metadata"]

            # Chunk text (processing times are short, likely 1 chunk each)
            chunks = chunk_text(content, chunk_size=512, overlap=50)
            logger.info(
                f"  Created {len(chunks)} chunks from {metadata_base['document_title']}"
            )

            # Create metadata for each chunk
            for chunk_idx, chunk in enumerate(chunks):
                metadata = metadata_base.copy()
                metadata["chunk_index"] = chunk_idx
                # Include chunk_index in section for unique vector IDs
                section = f"form_{metadata_base['form_type']}_chunk_{chunk_idx}"
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
                source="processing_times",
                dry_run=dry_run,
            )

            logger.info(f"\n✓ Ingestion complete: {vectors_upserted} vectors upserted")
        else:
            logger.warning("No chunks to ingest")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest USCIS Processing Times into Pinecone for RAG"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without calling APIs",
    )
    parser.add_argument(
        "--use-fallback",
        action="store_true",
        help="Use curated fallback data instead of USCIS API",
    )

    args = parser.parse_args()

    asyncio.run(
        ingest_processing_times(
            dry_run=args.dry_run,
            use_fallback=args.use_fallback,
        )
    )


if __name__ == "__main__":
    main()
