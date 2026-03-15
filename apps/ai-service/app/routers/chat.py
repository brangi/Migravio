import json
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.models.schemas import ChatRequest
from app.services.firebase_admin import verify_token, get_db
from app.services.escalation import detect_escalation
from app.services.ai_router import select_model, build_system_prompt, stream_chat
from app.services.rag import retrieve_context
from app.services.cache import get_cached_response, store_cached_response

router = APIRouter()

FREE_MESSAGE_LIMIT = 10


async def check_message_limit(uid: str, plan: str) -> bool:
    """Check if user has messages remaining. Returns True if allowed."""
    if plan in ("pro", "premium"):
        return True

    db = get_db()
    if db is None:
        return True  # Fail open if DB unavailable

    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return True

    data = user_doc.to_dict()
    count = data.get("messageCount", 0)
    reset_date = data.get("messageResetDate")

    # Reset monthly counter if needed
    if reset_date:
        reset_dt = reset_date if isinstance(reset_date, datetime) else reset_date.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now.month != reset_dt.month or now.year != reset_dt.year:
            user_ref.update({
                "messageCount": 0,
                "messageResetDate": now,
            })
            return True

    return count < FREE_MESSAGE_LIMIT


async def increment_message_count(uid: str):
    """Increment the user's monthly message count."""
    db = get_db()
    if db is None:
        return
    from google.cloud.firestore_v1 import Increment
    db.collection("users").document(uid).update({
        "messageCount": Increment(1),
    })


async def save_message(uid: str, session_id: str, role: str, content: str, model: str | None = None, escalated: bool = False):
    """Save a message to the user's chat session."""
    db = get_db()
    if db is None:
        return

    session_ref = db.collection("users").document(uid).collection("chatSessions").document(session_id)
    session_doc = session_ref.get()

    msg = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc),
    }
    if model:
        msg["model"] = model
    if escalated:
        msg["escalated"] = True

    if not session_doc.exists:
        session_ref.set({
            "title": content[:50] if role == "user" else "New conversation",
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc),
            "messages": [msg],
        })
    else:
        from google.cloud.firestore_v1 import ArrayUnion
        session_ref.update({
            "messages": ArrayUnion([msg]),
            "updatedAt": datetime.now(timezone.utc),
        })


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    authorization: str = Header(...),
):
    """Stream AI chat responses with RAG + escalation detection."""
    # Verify auth
    token = authorization.replace("Bearer ", "")
    claims = verify_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")

    uid = claims["uid"]

    # Get user profile for subscription check
    db = get_db()
    plan = "free"
    if db:
        user_doc = db.collection("users").document(uid).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            plan = user_data.get("subscription", {}).get("plan", "free")

    # Check message limit
    allowed = await check_message_limit(uid, plan)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Monthly message limit reached. Upgrade to Pro for unlimited messages.",
        )

    message = request.message
    language = request.language
    visa_type = request.visa_type
    session_id = request.session_id or uid  # Fallback to uid if no session

    # Check semantic cache first
    cached = await get_cached_response(message, language, visa_type)
    if cached:
        escalation = detect_escalation(message)

        async def cached_stream():
            yield json.dumps({
                "type": "content",
                "data": cached,
            })
            if escalation.is_escalation:
                yield json.dumps({
                    "type": "escalation",
                    "keywords": escalation.keywords_found,
                })
            yield json.dumps({"type": "done"})

        # Increment message count (frontend handles session storage)
        await increment_message_count(uid)

        return EventSourceResponse(cached_stream())

    # Detect escalation
    escalation = detect_escalation(message)

    # Select model based on complexity
    model = select_model(message)

    # Retrieve RAG context
    rag_context = await retrieve_context(message, visa_type)

    # Build system prompt
    system_prompt = build_system_prompt(language, visa_type, rag_context)

    # Load chat history for context
    history = []
    if db:
        try:
            session_doc = db.collection("users").document(uid).collection("chatSessions").document(session_id).get()
            if session_doc.exists:
                messages = session_doc.to_dict().get("messages", [])
                history = [{"role": m["role"], "content": m["content"]} for m in messages]
        except Exception:
            pass

    async def event_stream():
        full_response = ""

        try:
            # Stream model info
            yield json.dumps({"type": "model", "data": model})

            # Stream content
            async for token in stream_chat(message, history, system_prompt, model):
                full_response += token
                yield json.dumps({"type": "content", "data": token})

            # Send escalation flag if detected
            if escalation.is_escalation:
                yield json.dumps({
                    "type": "escalation",
                    "keywords": escalation.keywords_found,
                })

            yield json.dumps({"type": "done"})

            # Post-stream: increment count + cache (frontend handles session storage)
            await increment_message_count(uid)
            await store_cached_response(message, full_response, language, visa_type)
        except Exception as e:
            print(f"Streaming error: {e}")
            yield json.dumps({"type": "error", "data": str(e)})

    return EventSourceResponse(event_stream())
