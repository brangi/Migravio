import json
import hashlib
from datetime import datetime, timedelta, timezone

import numpy as np

from app.services.firebase_admin import get_db
from app.services.rag import get_embedding

CACHE_COLLECTION = "cache/semanticCache/entries"
SIMILARITY_THRESHOLD = 0.92
TTL_DAYS = 7


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


def cache_key(query: str, language: str, visa_type: str) -> str:
    """Generate a deterministic cache key."""
    raw = f"{query.lower().strip()}|{language}|{visa_type}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def get_cached_response(
    query: str, language: str, visa_type: str
) -> str | None:
    """Check Firestore semantic cache for a similar query."""
    db = get_db()
    if db is None:
        return None

    query_embedding = await get_embedding(query)
    if not query_embedding:
        return None

    try:
        # Check recent cache entries
        cutoff = datetime.now(timezone.utc) - timedelta(days=TTL_DAYS)
        docs = (
            db.collection(CACHE_COLLECTION)
            .where("language", "==", language)
            .where("createdAt", ">=", cutoff)
            .limit(50)
            .stream()
        )

        for doc in docs:
            data = doc.to_dict()
            stored_embedding = data.get("queryEmbedding", [])
            if not stored_embedding:
                continue

            similarity = cosine_similarity(query_embedding, stored_embedding)
            if similarity >= SIMILARITY_THRESHOLD:
                # Cache hit — update hit count
                doc.reference.update({"hitCount": data.get("hitCount", 0) + 1})
                return data.get("response")

        return None
    except Exception:
        return None


async def store_cached_response(
    query: str,
    response: str,
    language: str,
    visa_type: str,
) -> None:
    """Store a query-response pair in semantic cache."""
    db = get_db()
    if db is None:
        return

    query_embedding = await get_embedding(query)
    if not query_embedding:
        return

    try:
        key = cache_key(query, language, visa_type)
        db.collection(CACHE_COLLECTION).document(key).set({
            "query": query,
            "response": response,
            "queryEmbedding": query_embedding,
            "language": language,
            "visaType": visa_type,
            "createdAt": datetime.now(timezone.utc),
            "hitCount": 0,
        })
    except Exception:
        pass  # Cache write failure is non-critical
