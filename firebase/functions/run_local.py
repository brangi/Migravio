#!/usr/bin/env python3
"""
Local testing script for government scrapers.

Usage:
    python run_local.py --source uscis
    python run_local.py --source dhs
    python run_local.py --source state_dept
    python run_local.py --source all
    python run_local.py --source uscis --dry-run
"""

import argparse
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict
import json

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up environment
from dotenv import load_dotenv
load_dotenv()

# Firebase Admin setup
import firebase_admin
from firebase_admin import credentials, firestore

# Import scrapers and processors
from scrapers import (
    scrape_uscis_alerts,
    scrape_uscis_policy_manual,
    scrape_uscis_processing_times,
    scrape_dhs_news,
    scrape_state_dept_visa_bulletin,
    scrape_state_dept_advisories,
)
from processors import (
    detect_changes,
    update_stored_content,
    mark_unchanged_items_scraped,
    summarize_changes_sync,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_firebase() -> firestore.Client:
    """Initialize Firebase Admin SDK with service account credentials."""
    service_account_json = os.getenv('FIREBASE_ADMIN_SERVICE_ACCOUNT')

    if not service_account_json:
        logger.error("FIREBASE_ADMIN_SERVICE_ACCOUNT environment variable not set")
        sys.exit(1)

    try:
        # Parse service account JSON
        service_account = json.loads(service_account_json)

        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account)
            firebase_admin.initialize_app(cred)

        return firestore.client()

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in FIREBASE_ADMIN_SERVICE_ACCOUNT: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
        sys.exit(1)


def run_uscis_scrape(dry_run: bool = False) -> None:
    """Run USCIS scraping pipeline."""
    logger.info("=== Running USCIS Scrape ===")

    try:
        # Scrape all USCIS sources
        logger.info("Scraping USCIS alerts...")
        alerts = scrape_uscis_alerts()

        logger.info("Scraping USCIS policy manual...")
        policy_updates = scrape_uscis_policy_manual()

        logger.info("Scraping USCIS processing times...")
        processing_times = scrape_uscis_processing_times()

        # Summary
        logger.info(f"\nScraped Results:")
        logger.info(f"  - Alerts: {len(alerts)}")
        logger.info(f"  - Policy Updates: {len(policy_updates)}")
        logger.info(f"  - Processing Times: {len(processing_times)}")

        if dry_run:
            logger.info("\n=== DRY RUN - Sample Results ===")
            print_sample_items(alerts[:2], "USCIS Alerts")
            print_sample_items(policy_updates[:2], "Policy Updates")
            print_sample_items(processing_times[:1], "Processing Times")
            return

        # Process items (detect changes, summarize, store)
        db = initialize_firebase()

        logger.info("\nProcessing alerts...")
        process_scraped_items(alerts, 'uscis_alerts', db)

        logger.info("Processing policy updates...")
        process_scraped_items(policy_updates, 'uscis_policy_manual', db)

        logger.info("Processing processing times...")
        process_scraped_items(processing_times, 'uscis_processing_times', db)

        logger.info("\n=== USCIS Scrape Complete ===")

    except Exception as e:
        logger.error(f"Error in USCIS scrape: {e}", exc_info=True)
        sys.exit(1)


def run_dhs_scrape(dry_run: bool = False) -> None:
    """Run DHS scraping pipeline."""
    logger.info("=== Running DHS Scrape ===")

    try:
        logger.info("Scraping DHS news...")
        news_items = scrape_dhs_news()

        logger.info(f"\nScraped {len(news_items)} DHS news items")

        if dry_run:
            logger.info("\n=== DRY RUN - Sample Results ===")
            print_sample_items(news_items[:3], "DHS News")
            return

        db = initialize_firebase()

        logger.info("\nProcessing news items...")
        process_scraped_items(news_items, 'dhs_news', db)

        logger.info("\n=== DHS Scrape Complete ===")

    except Exception as e:
        logger.error(f"Error in DHS scrape: {e}", exc_info=True)
        sys.exit(1)


def run_state_dept_scrape(dry_run: bool = False) -> None:
    """Run State Department scraping pipeline."""
    logger.info("=== Running State Dept Scrape ===")

    try:
        logger.info("Scraping visa bulletins...")
        bulletins = scrape_state_dept_visa_bulletin()

        logger.info("Scraping travel advisories...")
        advisories = scrape_state_dept_advisories()

        logger.info(f"\nScraped Results:")
        logger.info(f"  - Visa Bulletins: {len(bulletins)}")
        logger.info(f"  - Advisories: {len(advisories)}")

        if dry_run:
            logger.info("\n=== DRY RUN - Sample Results ===")
            print_sample_items(bulletins[:2], "Visa Bulletins")
            print_sample_items(advisories[:2], "Travel Advisories")
            return

        db = initialize_firebase()

        logger.info("\nProcessing visa bulletins...")
        process_scraped_items(bulletins, 'state_dept_visa_bulletin', db)

        logger.info("Processing advisories...")
        process_scraped_items(advisories, 'state_dept_advisories', db)

        logger.info("\n=== State Dept Scrape Complete ===")

    except Exception as e:
        logger.error(f"Error in State Dept scrape: {e}", exc_info=True)
        sys.exit(1)


def process_scraped_items(items: List[Dict[str, str]], source: str, db: firestore.Client) -> None:
    """
    Process scraped items: detect changes, summarize, and store.

    Args:
        items: List of scraped items
        source: Source identifier
        db: Firestore client
    """
    if not items:
        logger.info(f"No items to process for '{source}'")
        return

    logger.info(f"Processing {len(items)} items from '{source}'")

    # Detect changes
    new_items, changed_items = detect_changes(items, source, db)

    all_urls = [item.get('url', '') for item in items]

    if not new_items and not changed_items:
        logger.info(f"No new or changed items for '{source}'")
        mark_unchanged_items_scraped(all_urls, source, db)
        return

    items_to_summarize = new_items + changed_items

    logger.info(f"Found {len(new_items)} new and {len(changed_items)} changed items")

    # Generate AI summaries
    try:
        logger.info("Generating AI summaries...")
        summarized_items = summarize_changes_sync(items_to_summarize)

        # Print sample summaries
        if summarized_items:
            logger.info("\nSample AI Summary:")
            sample = summarized_items[0]
            logger.info(f"  Title: {sample.get('title', '')[:60]}...")
            logger.info(f"  Summary: {sample.get('aiSummary', '')[:100]}...")
            logger.info(f"  Affects: {', '.join(sample.get('affectsVisaTypes', []))}")

    except Exception as e:
        logger.error(f"Error during AI summarization: {e}")
        summarized_items = items_to_summarize

    # Create policy alerts
    logger.info("Creating policy alerts...")
    create_policy_alerts(summarized_items, db)

    # Update stored content
    logger.info("Updating stored content...")
    update_stored_content(items_to_summarize, source, db)

    # Update unchanged items
    mark_unchanged_items_scraped(all_urls, source, db)

    logger.info(f"Processing complete for '{source}'")


def create_policy_alerts(items: List[Dict[str, str]], db: firestore.Client) -> None:
    """Create policy alert documents in Firestore."""
    if not items:
        return

    logger.info(f"Creating {len(items)} policy alerts")

    alerts_ref = db.collection('policyAlerts')
    now = datetime.utcnow()

    for item in items:
        try:
            import hashlib
            alert_id = hashlib.md5(item.get('url', '').encode()).hexdigest()

            alert_ref = alerts_ref.document(alert_id)
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
                alert_ref.update({**alert_data, 'updatedAt': now})
                logger.info(f"Updated alert: {item.get('title', '')[:40]}...")
            else:
                alert_ref.set({**alert_data, 'createdAt': now})
                logger.info(f"Created alert: {item.get('title', '')[:40]}...")

        except Exception as e:
            logger.error(f"Error creating alert: {e}")


def print_sample_items(items: List[Dict[str, str]], category: str) -> None:
    """Print sample scraped items for dry run."""
    if not items:
        logger.info(f"\n{category}: No items found")
        return

    logger.info(f"\n{category} (showing {len(items)} sample(s)):")
    for i, item in enumerate(items, 1):
        logger.info(f"\n  [{i}] {item.get('title', 'No title')}")
        logger.info(f"      Date: {item.get('date', 'Unknown')}")
        logger.info(f"      URL: {item.get('url', 'No URL')}")
        logger.info(f"      Summary: {item.get('summary', 'No summary')[:100]}...")


def main():
    """Main entry point for local scraper testing."""
    parser = argparse.ArgumentParser(description='Run immigration policy scrapers locally')
    parser.add_argument(
        '--source',
        choices=['uscis', 'dhs', 'state_dept', 'all'],
        required=True,
        help='Which source to scrape'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Scrape but do not store results (for testing)'
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Migravio Government Scraper - Local Test")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN MODE: Results will not be stored in Firestore")

    # Run requested scraper(s)
    if args.source == 'uscis' or args.source == 'all':
        run_uscis_scrape(args.dry_run)

    if args.source == 'dhs' or args.source == 'all':
        run_dhs_scrape(args.dry_run)

    if args.source == 'state_dept' or args.source == 'all':
        run_state_dept_scrape(args.dry_run)

    logger.info("\n" + "=" * 60)
    logger.info("Scraping complete!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
