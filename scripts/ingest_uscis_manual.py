"""
USCIS Policy Manual ingestion script for Migravio RAG pipeline.

Scrapes the USCIS Policy Manual (https://www.uscis.gov/policy-manual)
and ingests it into Pinecone for AI-assisted retrieval.

The USCIS Policy Manual is organized into 12 volumes with parts and chapters.
Each chunk is tagged with metadata including source, title, section, and
inferred visa types.

Usage:
    python scripts/ingest_uscis_manual.py [--dry-run] [--volumes 1,2,3]
"""

import argparse
import asyncio
import logging
import re
import time
from typing import Any

import httpx
from bs4 import BeautifulSoup

from shared import chunk_text, setup_clients, upsert_to_pinecone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Base URL for USCIS Policy Manual
USCIS_MANUAL_BASE_URL = "https://www.uscis.gov/policy-manual"

# Volume structure (12 volumes)
VOLUMES = {
    1: "General Policies and Procedures",
    2: "Nonimmigrants",
    3: "Employment Authorization",
    4: "Reserved for Future Use",
    5: "Employment-Based",
    6: "Immigrants",
    7: "Adjustment of Status",
    8: "Admissibility",
    9: "Waivers and Other Forms of Relief",
    10: "Reserved for Future Use",
    11: "Reserved for Future Use",
    12: "Citizenship and Naturalization",
}

# Visa type keywords for metadata tagging
VISA_TYPE_KEYWORDS = {
    "H-1B": ["h-1b", "h1b", "specialty occupation"],
    "H-4": ["h-4", "h4", "h-1b dependent"],
    "L-1": ["l-1", "l1", "intracompany transfer"],
    "O-1": ["o-1", "o1", "extraordinary ability"],
    "F-1": ["f-1", "f1", "student visa", "academic student"],
    "OPT": ["opt", "optional practical training"],
    "EB-1": ["eb-1", "eb1", "first preference"],
    "EB-2": ["eb-2", "eb2", "second preference"],
    "EB-3": ["eb-3", "eb3", "third preference"],
    "Green Card": ["green card", "lawful permanent resident", "lpr"],
    "Naturalization": ["naturalization", "citizenship", "n-400"],
}


def infer_visa_types(text: str) -> list[str]:
    """
    Infer visa types from text content using keyword matching.

    Args:
        text: Text to analyze

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
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.text
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def extract_chapter_links(html: str, volume: int) -> list[dict[str, str]]:
    """
    Extract chapter links from a volume page.

    Args:
        html: HTML content of volume page
        volume: Volume number

    Returns:
        List of dicts with 'url', 'title', 'part', 'chapter' keys
    """
    soup = BeautifulSoup(html, "html.parser")
    chapters = []

    # Find links specifically for this volume (filter out sidebar links to other volumes)
    volume_pattern = re.compile(rf"/policy-manual/volume-{volume}(?:-|$)")
    links = soup.find_all("a", href=volume_pattern)

    seen_urls = set()
    for link in links:
        href = link.get("href", "")
        title = link.get_text(strip=True)

        if not href or not title:
            continue

        # Normalize URL
        full_url = f"https://www.uscis.gov{href}" if href.startswith("/") else href

        # Skip duplicates and the volume index page itself
        if full_url in seen_urls:
            continue
        if href.rstrip("/") == f"/policy-manual/volume-{volume}":
            continue
        seen_urls.add(full_url)

        # Parse part and chapter from URL
        # Example: /policy-manual/volume-2-part-b-chapter-3
        match = re.search(r"volume-(\d+)(?:-part-([a-z]+))?(?:-chapter-(\d+))?", href)
        if match:
            vol = match.group(1)
            part = match.group(2) or "general"
            chapter = match.group(3) or "0"

            # Only include links that have at least a part (skip bare volume links)
            if part != "general" or chapter != "0":
                chapters.append(
                    {
                        "url": full_url,
                        "title": title,
                        "part": part.upper(),
                        "chapter": chapter,
                        "volume": vol,
                    }
                )

    return chapters


def extract_text_content(html: str) -> str:
    """
    Extract main text content from a USCIS manual page.

    Args:
        html: HTML content of page

    Returns:
        Extracted text content
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove navigation, headers, footers
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    # Find main content area (USCIS uses various structures)
    main_content = soup.find("main") or soup.find("article") or soup.find("body")

    if not main_content:
        return ""

    # Extract text with basic formatting preserved
    text = main_content.get_text(separator="\n", strip=True)

    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)

    return text


async def scrape_volume(
    volume: int,
    client: httpx.AsyncClient,
    rate_limit_delay: float = 2.0,
) -> list[dict[str, Any]]:
    """
    Scrape all chapters from a volume of the USCIS Policy Manual.

    Args:
        volume: Volume number (1-12)
        client: httpx AsyncClient instance
        rate_limit_delay: Delay in seconds between requests

    Returns:
        List of dicts containing chapter content and metadata
    """
    volume_title = VOLUMES.get(volume, f"Volume {volume}")
    logger.info(f"Scraping Volume {volume}: {volume_title}")

    volume_url = f"{USCIS_MANUAL_BASE_URL}/volume-{volume}"

    # Fetch volume index page
    html = await fetch_page(volume_url, client)
    if not html:
        logger.warning(f"Failed to fetch volume {volume} index")
        return []

    # Extract chapter links
    chapters = extract_chapter_links(html, volume)
    logger.info(f"Found {len(chapters)} chapters in Volume {volume}")

    scraped_content = []

    for i, chapter_info in enumerate(chapters):
        logger.info(
            f"  Scraping chapter {i+1}/{len(chapters)}: {chapter_info['title']}"
        )

        # Rate limiting - be respectful to USCIS servers
        if i > 0:
            await asyncio.sleep(rate_limit_delay)

        chapter_html = await fetch_page(chapter_info["url"], client)
        if not chapter_html:
            continue

        text_content = extract_text_content(chapter_html)

        if not text_content or len(text_content) < 100:
            logger.warning(f"  Skipping chapter {chapter_info['title']} (insufficient content)")
            continue

        scraped_content.append(
            {
                "content": text_content,
                "metadata": {
                    "source": "uscis_manual",
                    "document_title": chapter_info["title"],
                    "volume": str(volume),
                    "volume_title": volume_title,
                    "part": chapter_info["part"],
                    "chapter": chapter_info["chapter"],
                    "section": f"volume_{volume}_part_{chapter_info['part']}_chapter_{chapter_info['chapter']}",
                },
            }
        )

    return scraped_content


async def ingest_uscis_manual(
    volumes: list[int] | None = None,
    dry_run: bool = False,
    rate_limit_delay: float = 2.0,
):
    """
    Main ingestion function for USCIS Policy Manual.

    Args:
        volumes: List of volume numbers to ingest (default: all)
        dry_run: If True, skip actual API calls
        rate_limit_delay: Delay in seconds between requests
    """
    if volumes is None:
        volumes = list(VOLUMES.keys())

    # Filter out reserved volumes
    volumes = [v for v in volumes if VOLUMES.get(v) != "Reserved for Future Use"]

    logger.info(f"Starting USCIS Policy Manual ingestion for volumes: {volumes}")
    logger.info(f"Dry run: {dry_run}")

    # Initialize clients
    clients = await setup_clients()

    # Create HTTP client
    total_vectors = 0

    async with httpx.AsyncClient() as http_client:
        for volume in volumes:
            # Scrape volume
            scraped_content = await scrape_volume(volume, http_client, rate_limit_delay)

            if not scraped_content:
                logger.warning(f"No content scraped from volume {volume}")
                continue

            # Chunk and prepare for ingestion — per volume
            vol_chunks = []
            vol_metadata = []

            for item in scraped_content:
                content = item["content"]
                metadata_base = item["metadata"]

                # Chunk text
                chunks = chunk_text(content, chunk_size=512, overlap=50)
                logger.info(
                    f"  Created {len(chunks)} chunks from {metadata_base['document_title']}"
                )

                # Infer visa types from content
                visa_types = infer_visa_types(content)

                # Create metadata for each chunk
                for chunk_idx, chunk in enumerate(chunks):
                    metadata = metadata_base.copy()
                    metadata["chunk_index"] = chunk_idx
                    metadata["visa_types"] = visa_types
                    # Include chunk_index in section for unique vector IDs
                    metadata["section"] = f"{metadata_base['section']}_chunk_{chunk_idx}"

                    vol_chunks.append(chunk)
                    vol_metadata.append(metadata)

            # Upsert this volume's data to Pinecone immediately
            if vol_chunks:
                logger.info(f"Upserting {len(vol_chunks)} chunks from Volume {volume}")

                vectors_upserted = await upsert_to_pinecone(
                    clients.index,
                    vol_chunks,
                    vol_metadata,
                    source="uscis_manual",
                    dry_run=dry_run,
                )

                total_vectors += vectors_upserted
                logger.info(f"✓ Volume {volume}: {vectors_upserted} vectors upserted (total: {total_vectors})")

    if total_vectors > 0:
        logger.info(f"\n✓ Ingestion complete: {total_vectors} total vectors upserted")
    else:
        logger.warning("No chunks to ingest")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest USCIS Policy Manual into Pinecone for RAG"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be ingested without calling APIs",
    )
    parser.add_argument(
        "--volumes",
        type=str,
        help="Comma-separated list of volume numbers to ingest (e.g., '1,2,3')",
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=2.0,
        help="Delay in seconds between requests (default: 2.0)",
    )

    args = parser.parse_args()

    volumes = None
    if args.volumes:
        volumes = [int(v.strip()) for v in args.volumes.split(",")]

    asyncio.run(
        ingest_uscis_manual(
            volumes=volumes,
            dry_run=args.dry_run,
            rate_limit_delay=args.rate_limit,
        )
    )


if __name__ == "__main__":
    main()
