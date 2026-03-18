from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None
    language: str = Field(default="en", pattern=r"^(en|es)$")
    visa_type: str = Field(default="", max_length=50)


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class EscalationResult(BaseModel):
    is_escalation: bool
    keywords_found: list[str]
