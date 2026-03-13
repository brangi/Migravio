from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def chat_placeholder():
    """Placeholder — streaming chat implemented in Sub-Project 2."""
    return {"message": "Chat endpoint coming soon"}
