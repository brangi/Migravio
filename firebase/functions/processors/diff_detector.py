"""
Change detection for scraped content using content hashing.

Compares newly scraped items against stored content in Firestore
to identify what's new or changed.
"""

import logging
import hashlib
from typing import List, Dict, Tuple
from datetime import datetime
from firebase_admin import firestore

logger = logging.getLogger(__name__)


def generate_content_hash(item: Dict[str, str]) -> str:
    """
    Generate SHA256 hash of scraped item content.

    Hashes the combination of title and summary to detect meaningful changes.
    URL and date are not included in hash since they may change without
    meaningful content changes.

    Args:
        item: Scraped item dict with 'title' and 'summary' keys

    Returns:
        Hex string of SHA256 hash
    """
    content = f"{item.get('title', '')}||{item.get('summary', '')}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def detect_changes(
    scraped_items: List[Dict[str, str]],
    source: str,
    db: firestore.Client
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Detect which scraped items are new or changed compared to stored content.

    Args:
        scraped_items: List of newly scraped items
        source: Source identifier (e.g., 'uscis_alerts', 'dhs_news')
        db: Firestore client instance

    Returns:
        Tuple of (new_items, changed_items)
        - new_items: Items not seen before
        - changed_items: Items with same URL but different content
    """
    logger.info(f"Detecting changes for {len(scraped_items)} items from {source}")

    new_items = []
    changed_items = []

    # Get stored content for this source
    stored_content_ref = db.collection('scrapedContent')
    stored_docs = {}

    try:
        # Query all documents for this source
        query = stored_content_ref.where('source', '==', source).stream()

        for doc in query:
            data = doc.to_dict()
            # Index by URL for quick lookup
            stored_docs[data.get('url', '')] = {
                'id': doc.id,
                'contentHash': data.get('contentHash', ''),
                'lastChangedAt': data.get('lastChangedAt'),
            }

        logger.info(f"Found {len(stored_docs)} stored items for source '{source}'")

    except Exception as e:
        logger.error(f"Error querying stored content: {e}")
        # If we can't query, treat all items as new
        return scraped_items, []

    # Compare each scraped item
    for item in scraped_items:
        item_url = item.get('url', '')
        content_hash = generate_content_hash(item)

        if item_url in stored_docs:
            # Item exists - check if content changed
            stored = stored_docs[item_url]
            if stored['contentHash'] != content_hash:
                # Content has changed
                logger.info(f"Content changed for: {item.get('title', 'Unknown')}")
                changed_items.append({
                    **item,
                    '_storedId': stored['id'],
                    '_oldHash': stored['contentHash'],
                    '_newHash': content_hash,
                })
            else:
                # No change - skip
                logger.debug(f"No change for: {item.get('title', 'Unknown')}")
        else:
            # New item
            logger.info(f"New item found: {item.get('title', 'Unknown')}")
            new_items.append({
                **item,
                '_newHash': content_hash,
            })

    logger.info(f"Change detection complete: {len(new_items)} new, {len(changed_items)} changed")
    return new_items, changed_items


def update_stored_content(
    items: List[Dict[str, str]],
    source: str,
    db: firestore.Client
) -> None:
    """
    Update Firestore with new/changed content hashes.

    Args:
        items: List of items to store (should have '_newHash' key added by detect_changes)
        source: Source identifier
        db: Firestore client instance
    """
    if not items:
        logger.info("No items to update in stored content")
        return

    logger.info(f"Updating stored content for {len(items)} items from {source}")

    stored_content_ref = db.collection('scrapedContent')
    now = datetime.utcnow()

    batch = db.batch()
    batch_count = 0
    max_batch_size = 500  # Firestore batch limit

    for item in items:
        try:
            # Check if this is an update (has _storedId) or new item
            if '_storedId' in item:
                # Update existing document
                doc_ref = stored_content_ref.document(item['_storedId'])
                batch.update(doc_ref, {
                    'contentHash': item['_newHash'],
                    'rawContent': item.get('summary', ''),
                    'title': item.get('title', ''),
                    'lastScrapedAt': now,
                    'lastChangedAt': now,
                })
            else:
                # Create new document
                # Use URL-based ID for consistency
                doc_id = hashlib.md5(item.get('url', '').encode()).hexdigest()
                doc_ref = stored_content_ref.document(doc_id)

                batch.set(doc_ref, {
                    'source': source,
                    'url': item.get('url', ''),
                    'title': item.get('title', ''),
                    'contentHash': item['_newHash'],
                    'rawContent': item.get('summary', ''),
                    'lastScrapedAt': now,
                    'lastChangedAt': now,
                    'publishedAt': item.get('date', now.isoformat()),
                })

            batch_count += 1

            # Commit batch if we hit the limit
            if batch_count >= max_batch_size:
                batch.commit()
                logger.info(f"Committed batch of {batch_count} updates")
                batch = db.batch()
                batch_count = 0

        except Exception as e:
            logger.error(f"Error preparing update for item: {e}")
            continue

    # Commit remaining items
    if batch_count > 0:
        try:
            batch.commit()
            logger.info(f"Committed final batch of {batch_count} updates")
        except Exception as e:
            logger.error(f"Error committing final batch: {e}")

    logger.info("Stored content update complete")


def mark_unchanged_items_scraped(
    scraped_urls: List[str],
    source: str,
    db: firestore.Client
) -> None:
    """
    Update lastScrapedAt timestamp for items that haven't changed.

    This tracks that we checked these items even though content didn't change.

    Args:
        scraped_urls: List of URLs that were scraped
        source: Source identifier
        db: Firestore client instance
    """
    if not scraped_urls:
        return

    logger.info(f"Marking {len(scraped_urls)} unchanged items as scraped")

    stored_content_ref = db.collection('scrapedContent')
    now = datetime.utcnow()

    # Update in batches
    batch = db.batch()
    batch_count = 0

    try:
        query = stored_content_ref.where('source', '==', source).stream()

        for doc in query:
            data = doc.to_dict()
            if data.get('url') in scraped_urls:
                batch.update(doc.reference, {
                    'lastScrapedAt': now,
                })
                batch_count += 1

                if batch_count >= 500:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0

        if batch_count > 0:
            batch.commit()

        logger.info(f"Updated lastScrapedAt for {batch_count} items")

    except Exception as e:
        logger.error(f"Error updating lastScrapedAt timestamps: {e}")
