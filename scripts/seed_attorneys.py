#!/usr/bin/env python3
"""
Seed founding attorney profiles into Firestore.

Usage:
    python scripts/seed_attorneys.py
    python scripts/seed_attorneys.py --dry-run

Requires FIREBASE_ADMIN_SERVICE_ACCOUNT env var (JSON string or file path).
"""

import json
import os
import sys
from datetime import datetime

# Add parent dir to path for shared imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    print("ERROR: firebase-admin not installed. Run: pip install firebase-admin")
    sys.exit(1)

ATTORNEYS = [
    {
        "name": "Maria Rodriguez",
        "email": "maria@example.com",
        "phone": "(555) 100-0001",
        "specialty": ["Family-Based", "Naturalization", "DACA"],
        "languagesSpoken": ["English", "Spanish"],
        "statesLicensed": ["California", "Texas"],
        "bio": "15+ years of experience in family-based immigration and naturalization. Passionate about helping families stay together through the immigration process.",
        "profilePhoto": "",
        "active": True,
    },
    {
        "name": "David Chen",
        "email": "david@example.com",
        "phone": "(555) 100-0002",
        "specialty": ["Employment-Based", "H-1B", "O-1", "EB-1"],
        "languagesSpoken": ["English", "Mandarin"],
        "statesLicensed": ["New York", "New Jersey"],
        "bio": "Former Big Law attorney specializing in employment-based immigration. Expert in H-1B, O-1 extraordinary ability, and EB-1 green card cases.",
        "profilePhoto": "",
        "active": True,
    },
    {
        "name": "Sarah Williams",
        "email": "sarah@example.com",
        "phone": "(555) 100-0003",
        "specialty": ["Asylum", "Removal Defense", "VAWA"],
        "languagesSpoken": ["English", "French"],
        "statesLicensed": ["Florida", "Georgia"],
        "bio": "Dedicated immigration attorney focused on humanitarian cases including asylum, removal defense, and VAWA protections for domestic violence survivors.",
        "profilePhoto": "",
        "active": True,
    },
    {
        "name": "Raj Patel",
        "email": "raj@example.com",
        "phone": "(555) 100-0004",
        "specialty": ["Employment-Based", "H-1B", "L-1", "EB-2/EB-3"],
        "languagesSpoken": ["English", "Hindi", "Gujarati"],
        "statesLicensed": ["California", "Washington"],
        "bio": "10+ years helping tech professionals navigate the H-1B, L-1, and employment-based green card process. Deep expertise in STEM immigration.",
        "profilePhoto": "",
        "active": True,
    },
    {
        "name": "Ana Gutierrez",
        "email": "ana@example.com",
        "phone": "(555) 100-0005",
        "specialty": ["Family-Based", "Consular Processing", "Waivers"],
        "languagesSpoken": ["English", "Spanish"],
        "statesLicensed": ["Texas", "Arizona", "New Mexico"],
        "bio": "Specializes in family-based petitions, consular processing, and unlawful presence waivers. Bilingual practice serving the border region.",
        "profilePhoto": "",
        "active": True,
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
        # Try as JSON string
        cred_dict = json.loads(sa)
        cred = credentials.Certificate(cred_dict)
    except (json.JSONDecodeError, ValueError):
        # Try as file path
        if os.path.isfile(sa):
            cred = credentials.Certificate(sa)
        else:
            print(f"ERROR: Could not parse FIREBASE_ADMIN_SERVICE_ACCOUNT as JSON or find file: {sa}")
            sys.exit(1)

    firebase_admin.initialize_app(cred)
    return firestore.client()


def seed_attorneys(db_client, dry_run=False):
    """Seed attorney profiles into Firestore."""
    print(f"Seeding {len(ATTORNEYS)} attorney profiles...")
    if dry_run:
        print("(DRY RUN - no data will be written)")

    for i, attorney in enumerate(ATTORNEYS, 1):
        doc_data = {
            **attorney,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
        }

        if dry_run:
            print(f"  [{i}/{len(ATTORNEYS)}] Would create: {attorney['name']}")
            print(f"    Specialties: {', '.join(attorney['specialty'])}")
            print(f"    Languages: {', '.join(attorney['languagesSpoken'])}")
            print(f"    States: {', '.join(attorney['statesLicensed'])}")
        else:
            doc_ref = db_client.collection("attorneys").document()
            doc_ref.set(doc_data)
            print(f"  [{i}/{len(ATTORNEYS)}] Created: {attorney['name']} (ID: {doc_ref.id})")

    print(f"\nDone! {len(ATTORNEYS)} attorneys {'would be' if dry_run else ''} seeded.")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN MODE ===\n")
        for i, attorney in enumerate(ATTORNEYS, 1):
            print(f"  [{i}] {attorney['name']}")
            print(f"      Specialties: {', '.join(attorney['specialty'])}")
            print(f"      Languages: {', '.join(attorney['languagesSpoken'])}")
            print(f"      States: {', '.join(attorney['statesLicensed'])}")
            print()
        print(f"Total: {len(ATTORNEYS)} attorneys")
        print("\nTo actually seed, run without --dry-run")
    else:
        db_client = init_firebase()
        seed_attorneys(db_client)
