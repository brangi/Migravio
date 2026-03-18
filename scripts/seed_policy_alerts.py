#!/usr/bin/env python3
"""
Seed policy alerts into Firestore policyAlerts collection.

Usage:
    python scripts/seed_policy_alerts.py
    python scripts/seed_policy_alerts.py --dry-run

Requires FIREBASE_ADMIN_SERVICE_ACCOUNT env var (JSON string or file path).
"""

import hashlib
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("ERROR: firebase-admin not installed. Run: pip install firebase-admin")
    sys.exit(1)

ALERTS = [
    {
        "title": "USCIS Opens H-1B Electronic Registration for FY 2027",
        "summary": "USCIS has opened the H-1B electronic registration period for fiscal year 2027. Employers and their representatives can submit registrations for prospective H-1B workers. The registration period runs from early March through late March 2026. Only selected registrations will be eligible to file H-1B cap petitions. USCIS continues to use the beneficiary-centric selection process to reduce duplicate registrations.",
        "source": "uscis_alerts",
        "sourceUrl": "https://www.uscis.gov/newsroom/alerts/uscis-opens-h-1b-electronic-registration",
        "affectsVisaTypes": ["H-1B"],
        "publishedAt": "2026-03-01T12:00:00Z",
    },
    {
        "title": "USCIS Adjusts Filing Fees for Immigration Benefit Requests",
        "summary": "USCIS has implemented updated filing fees for several immigration forms effective in 2026. The fee adjustments affect commonly filed forms including I-485 (Adjustment of Status), I-130 (Petition for Alien Relative), I-765 (Employment Authorization), and N-400 (Naturalization). Applicants should verify current fees on uscis.gov before filing. Fee waivers remain available for eligible applicants who can demonstrate financial hardship.",
        "source": "uscis_alerts",
        "sourceUrl": "https://www.uscis.gov/newsroom/alerts/uscis-adjusts-fees-for-immigration-services",
        "affectsVisaTypes": ["General"],
        "publishedAt": "2026-02-15T12:00:00Z",
    },
    {
        "title": "DHS Extends and Redesignates TPS for Select Countries",
        "summary": "The Department of Homeland Security has extended and redesignated Temporary Protected Status for several countries due to ongoing armed conflict and extraordinary conditions. Current TPS holders must re-register during the designated period to maintain their status and employment authorization. New applicants from redesignated countries who have been continuously residing in the U.S. since the redesignation date may also apply.",
        "source": "dhs_news",
        "sourceUrl": "https://www.uscis.gov/newsroom/alerts/tps-redesignation-2026",
        "affectsVisaTypes": ["TPS"],
        "publishedAt": "2026-02-28T12:00:00Z",
    },
    {
        "title": "USCIS Announces Improvements to Employment Authorization Document Processing",
        "summary": "USCIS has announced processing improvements for Employment Authorization Document (EAD) applications. The agency is reducing processing times for Form I-765 across several eligibility categories including H-4 dependent spouses, L-2 dependent spouses, and F-1 students applying for Optional Practical Training. Automatic EAD extensions continue to apply for eligible renewal applicants while their applications are pending.",
        "source": "uscis_alerts",
        "sourceUrl": "https://www.uscis.gov/newsroom/alerts/ead-processing-improvements-2026",
        "affectsVisaTypes": ["H-4", "L-2", "F-1", "OPT"],
        "publishedAt": "2026-03-10T12:00:00Z",
    },
    {
        "title": "March 2026 Visa Bulletin Shows Movement in Employment-Based Categories",
        "summary": "The Department of State has released the March 2026 Visa Bulletin showing forward movement in several employment-based preference categories. EB-2 and EB-3 categories for India and China have advanced, potentially allowing more applicants to file adjustment of status applications. Applicants should check both the Final Action Dates and Dates for Filing charts to determine their eligibility. USCIS has confirmed it will use the Dates for Filing chart for March 2026.",
        "source": "state_dept",
        "sourceUrl": "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin/2026/visa-bulletin-for-march-2026.html",
        "affectsVisaTypes": ["Green Card", "EB-1", "EB-2", "EB-3"],
        "publishedAt": "2026-03-05T12:00:00Z",
    },
]


def init_firebase():
    """Initialize Firebase Admin SDK."""
    sa = os.environ.get("FIREBASE_ADMIN_SERVICE_ACCOUNT", "")
    if not sa:
        print("ERROR: FIREBASE_ADMIN_SERVICE_ACCOUNT env var not set.")
        print("Set it to a JSON string or path to a service account JSON file.")
        sys.exit(1)

    try:
        cred_dict = json.loads(sa)
        cred = credentials.Certificate(cred_dict)
    except (json.JSONDecodeError, ValueError):
        if os.path.isfile(sa):
            cred = credentials.Certificate(sa)
        else:
            print(f"ERROR: Could not parse FIREBASE_ADMIN_SERVICE_ACCOUNT as JSON or find file: {sa}")
            sys.exit(1)

    firebase_admin.initialize_app(cred)
    return firestore.client()


def seed_alerts(db_client, dry_run=False):
    """Seed policy alerts into Firestore."""
    print(f"Seeding {len(ALERTS)} policy alerts...")
    if dry_run:
        print("(DRY RUN - no data will be written)\n")

    now = datetime.utcnow()

    for i, alert in enumerate(ALERTS, 1):
        doc_id = hashlib.md5(alert["sourceUrl"].encode()).hexdigest()

        doc_data = {
            "title": alert["title"],
            "summary": alert["summary"],
            "aiSummary": alert["summary"],
            "source": alert["source"],
            "sourceUrl": alert["sourceUrl"],
            "affectsVisaTypes": alert["affectsVisaTypes"],
            "publishedAt": alert["publishedAt"],
            "scrapedAt": now,
            "active": True,
            "createdAt": now,
            "updatedAt": now,
        }

        if dry_run:
            print(f"  [{i}/{len(ALERTS)}] {alert['title']}")
            print(f"    ID: {doc_id}")
            print(f"    Affects: {', '.join(alert['affectsVisaTypes'])}")
            print(f"    Source: {alert['source']}")
            print()
        else:
            db_client.collection("policyAlerts").document(doc_id).set(doc_data)
            print(f"  [{i}/{len(ALERTS)}] Seeded: {alert['title']} (ID: {doc_id})")

    print(f"\nDone! {len(ALERTS)} alerts {'would be' if dry_run else ''} seeded.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN MODE ===\n")
        for i, alert in enumerate(ALERTS, 1):
            doc_id = hashlib.md5(alert["sourceUrl"].encode()).hexdigest()
            print(f"  [{i}] {alert['title']}")
            print(f"      ID: {doc_id}")
            print(f"      Affects: {', '.join(alert['affectsVisaTypes'])}")
            print(f"      Source: {alert['source']}")
            print()
        print(f"Total: {len(ALERTS)} alerts")
        print("\nTo actually seed, run without --dry-run")
    else:
        db_client = init_firebase()
        seed_alerts(db_client)
