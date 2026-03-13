import json

import firebase_admin
from firebase_admin import credentials, auth, firestore
from app.config import settings

_app = None
_db = None


def _init():
    global _app, _db
    if _app is not None:
        return

    if settings.firebase_admin_service_account:
        try:
            sa = json.loads(settings.firebase_admin_service_account)
            cred = credentials.Certificate(sa)
        except (json.JSONDecodeError, ValueError):
            # Might be a file path
            cred = credentials.Certificate(settings.firebase_admin_service_account)
    else:
        cred = credentials.ApplicationDefault()

    _app = firebase_admin.initialize_app(cred)
    _db = firestore.client()


def get_db():
    _init()
    return _db


def verify_token(id_token: str) -> dict | None:
    """Verify a Firebase ID token and return the decoded claims."""
    _init()
    try:
        decoded = auth.verify_id_token(id_token)
        return decoded
    except Exception:
        return None
