"""
Firebase Cloud Functions for government website scraping.

Scheduled functions that monitor USCIS, DHS, and State Department
for immigration policy updates.
"""

import logging
import os
from datetime import datetime
from typing import List, Dict

# Firebase imports
from firebase_functions import scheduler_fn
import firebase_admin
from firebase_admin import firestore

# Local imports
from scrapers import (
    scrape_uscis_alerts,
    scrape_uscis_policy_manual,
    scrape_uscis_processing_times,
    scrape_dhs_news,
    scrape_state_dept_visa_bulletin,
    scrape_state_dept_advisories,
    refresh_pinecone_vectors,
)
from processors import (
    detect_changes,
    update_stored_content,
    mark_unchanged_items_scraped,
    summarize_changes_sync,
)

# Initialize Firebase Admin (auto-initializes in Cloud Functions environment)
if not firebase_admin._apps:
    firebase_admin.initialize_app()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@scheduler_fn.on_schedule(schedule="every 6 hours")
def scrape_uscis(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Scrape USCIS for policy updates, news, and processing times.

    Runs every 6 hours to check for new content.
    """
    logger.info("=== Starting USCIS scrape job ===")

    try:
        # Scrape all USCIS sources
        alerts = scrape_uscis_alerts()
        policy_updates = scrape_uscis_policy_manual()
        processing_times = scrape_uscis_processing_times()

        # Combine all items
        all_items = alerts + policy_updates + processing_times

        logger.info(f"Scraped total of {len(all_items)} items from USCIS")

        if not all_items:
            logger.warning("No items scraped from USCIS")
            return

        # Process each source separately to maintain separate stored content
        process_scraped_items(alerts, 'uscis_alerts')
        process_scraped_items(policy_updates, 'uscis_policy_manual')
        process_scraped_items(processing_times, 'uscis_processing_times')

        logger.info("=== USCIS scrape job completed successfully ===")

    except Exception as e:
        logger.error(f"Error in USCIS scrape job: {e}", exc_info=True)
        raise


@scheduler_fn.on_schedule(schedule="every 6 hours")
def scrape_dhs(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Scrape DHS for immigration-related press releases.

    Runs every 6 hours to check for new content.
    """
    logger.info("=== Starting DHS scrape job ===")

    try:
        news_items = scrape_dhs_news()

        logger.info(f"Scraped {len(news_items)} items from DHS")

        if not news_items:
            logger.warning("No items scraped from DHS")
            return

        process_scraped_items(news_items, 'dhs_news')

        logger.info("=== DHS scrape job completed successfully ===")

    except Exception as e:
        logger.error(f"Error in DHS scrape job: {e}", exc_info=True)
        raise


@scheduler_fn.on_schedule(schedule="every 6 hours")
def scrape_state_dept(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Scrape State Department for visa bulletins and advisories.

    Runs every 6 hours to check for new content.
    """
    logger.info("=== Starting State Dept scrape job ===")

    try:
        bulletins = scrape_state_dept_visa_bulletin()
        advisories = scrape_state_dept_advisories()

        all_items = bulletins + advisories

        logger.info(f"Scraped {len(all_items)} items from State Dept")

        if not all_items:
            logger.warning("No items scraped from State Dept")
            return

        process_scraped_items(bulletins, 'state_dept_visa_bulletin')
        process_scraped_items(advisories, 'state_dept_advisories')

        logger.info("=== State Dept scrape job completed successfully ===")

    except Exception as e:
        logger.error(f"Error in State Dept scrape job: {e}", exc_info=True)
        raise


def process_scraped_items(items: List[Dict[str, str]], source: str) -> None:
    """
    Process scraped items: detect changes, summarize, and store.

    Args:
        items: List of scraped items
        source: Source identifier (e.g., 'uscis_alerts')
    """
    if not items:
        logger.info(f"No items to process for source '{source}'")
        return

    logger.info(f"Processing {len(items)} items from '{source}'")

    db = firestore.client()

    # Detect what's new or changed
    new_items, changed_items = detect_changes(items, source, db)

    # Track all scraped URLs to update lastScrapedAt for unchanged items
    all_urls = [item.get('url', '') for item in items]

    if not new_items and not changed_items:
        logger.info(f"No new or changed items for '{source}'")
        # Still update lastScrapedAt for unchanged items
        mark_unchanged_items_scraped(all_urls, source, db)
        return

    # Combine new and changed for AI processing
    items_to_summarize = new_items + changed_items

    logger.info(f"Found {len(new_items)} new and {len(changed_items)} changed items")

    # Generate AI summaries and extract visa types
    try:
        summarized_items = summarize_changes_sync(items_to_summarize)
    except Exception as e:
        logger.error(f"Error during AI summarization: {e}", exc_info=True)
        # Continue without AI summaries
        summarized_items = items_to_summarize

    # Create policy alerts in Firestore
    create_policy_alerts(summarized_items, db)

    # Update stored content with new hashes
    update_stored_content(items_to_summarize, source, db)

    # Update lastScrapedAt for unchanged items
    mark_unchanged_items_scraped(all_urls, source, db)

    logger.info(f"Completed processing for '{source}'")


def create_policy_alerts(items: List[Dict[str, str]], db: firestore.Client) -> None:
    """
    Create policy alert documents in Firestore.

    Args:
        items: Summarized items to create alerts for
        db: Firestore client
    """
    if not items:
        return

    logger.info(f"Creating {len(items)} policy alerts")

    alerts_ref = db.collection('policyAlerts')
    now = datetime.utcnow()

    batch = db.batch()
    batch_count = 0

    for item in items:
        try:
            # Create unique alert ID based on URL
            import hashlib
            alert_id = hashlib.md5(item.get('url', '').encode()).hexdigest()

            alert_ref = alerts_ref.document(alert_id)

            # Determine if this is an update to existing alert
            existing_alert = alert_ref.get()

            alert_data = {
                'title': item.get('title', ''),
                'summary': item.get('summary', '')[:500],
                'fullContent': item.get('summary', ''),
                'source': item.get('source', ''),
                'sourceUrl': item.get('url', ''),
                'affectsVisaTypes': item.get('affectsVisaTypes', ['General']),
                'publishedAt': item.get('date', now.isoformat()),
                'scrapedAt': now,
                'aiSummary': item.get('aiSummary', item.get('summary', '')[:500]),
                'active': True,
            }

            if existing_alert.exists:
                # Update existing alert
                batch.update(alert_ref, {
                    **alert_data,
                    'updatedAt': now,
                })
                logger.info(f"Updating existing alert: {item.get('title', '')[:50]}")
            else:
                # Create new alert
                batch.set(alert_ref, {
                    **alert_data,
                    'createdAt': now,
                })
                logger.info(f"Creating new alert: {item.get('title', '')[:50]}")

            batch_count += 1

            # Commit batch if we hit limit
            if batch_count >= 500:
                batch.commit()
                logger.info(f"Committed batch of {batch_count} alerts")
                batch = db.batch()
                batch_count = 0

        except Exception as e:
            logger.error(f"Error creating alert for item: {e}")
            continue

    # Commit remaining items
    if batch_count > 0:
        try:
            batch.commit()
            logger.info(f"Committed final batch of {batch_count} alerts")
        except Exception as e:
            logger.error(f"Error committing final batch: {e}")

    logger.info(f"Policy alert creation complete")


@scheduler_fn.on_schedule(
    schedule="0 3 1 * *",
    timeout_sec=540,
    memory=512,
)
def refresh_pinecone(event: scheduler_fn.ScheduledEvent) -> None:
    """
    Monthly refresh of Pinecone RAG vectors.

    Runs on the 1st of every month at 3am UTC.
    Re-ingests: Visa Bulletin, Processing Times, Federal Register rules.
    """
    logger.info("=== Starting monthly Pinecone refresh ===")

    try:
        results = refresh_pinecone_vectors()

        total = sum(v for v in results.values() if v > 0)
        failures = [k for k, v in results.items() if v < 0]

        logger.info(f"Pinecone refresh complete: {total} vectors upserted")
        for source, count in results.items():
            logger.info(f"  {source}: {count} vectors")

        if failures:
            logger.warning(f"Failed sources: {', '.join(failures)}")

        # Log results to Firestore
        db = firestore.client()
        db.collection("system_logs").add({
            "type": "pinecone_refresh",
            "results": results,
            "total_vectors": total,
            "failures": failures,
            "timestamp": datetime.utcnow(),
        })

        logger.info("=== Monthly Pinecone refresh completed ===")

    except Exception as e:
        logger.error(f"Pinecone refresh failed: {e}", exc_info=True)
        raise


# Optional: Manual trigger function for testing (HTTP endpoint)
# Uncomment when you want to test manually via HTTP
"""
from firebase_functions import https_fn

@https_fn.on_request()
def trigger_scrape_uscis(req: https_fn.Request) -> https_fn.Response:
    '''Manual trigger for USCIS scrape (for testing).'''
    try:
        scrape_uscis(None)
        return https_fn.Response("USCIS scrape completed", status=200)
    except Exception as e:
        logger.error(f"Manual trigger failed: {e}")
        return https_fn.Response(f"Error: {str(e)}", status=500)

@https_fn.on_request()
def trigger_scrape_dhs(req: https_fn.Request) -> https_fn.Response:
    '''Manual trigger for DHS scrape (for testing).'''
    try:
        scrape_dhs(None)
        return https_fn.Response("DHS scrape completed", status=200)
    except Exception as e:
        logger.error(f"Manual trigger failed: {e}")
        return https_fn.Response(f"Error: {str(e)}", status=500)

@https_fn.on_request()
def trigger_scrape_state_dept(req: https_fn.Request) -> https_fn.Response:
    '''Manual trigger for State Dept scrape (for testing).'''
    try:
        scrape_state_dept(None)
        return https_fn.Response("State Dept scrape completed", status=200)
    except Exception as e:
        logger.error(f"Manual trigger failed: {e}")
        return https_fn.Response(f"Error: {str(e)}", status=500)
"""
