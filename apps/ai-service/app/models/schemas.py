from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    language: str = "en"
    visa_type: str = ""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class EscalationResult(BaseModel):
    is_escalation: bool
    keywords_found: list[str]
