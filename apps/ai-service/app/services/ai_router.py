from openai import AsyncOpenAI
from app.config import settings
from app.services.escalation import detect_escalation

client = AsyncOpenAI(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
)


def select_model(message: str) -> str:
    """Route to Haiku (simple) or Sonnet (complex/escalation)."""
    escalation = detect_escalation(message)
    if escalation.is_escalation:
        return settings.model_complex
    # Short factual queries → Haiku
    if len(message.split()) < 30:
        return settings.model_simple
    return settings.model_complex


def build_system_prompt(language: str, visa_type: str, rag_context: str) -> str:
    lang_instruction = {
        "en": "Respond in English.",
        "es": "Responde en espanol.",
    }.get(language, "Respond in English.")

    visa_context = f"The user has a {visa_type} visa." if visa_type else ""

    return f"""You are Migravio, a warm, knowledgeable immigration assistant for the United States.

{lang_instruction}

{visa_context}

RULES:
- You provide legal INFORMATION, never legal ADVICE.
- Be warm, clear, and human — like a knowledgeable friend, not a legal textbook.
- Ground your answers in the provided context. If the context doesn't cover the question, say so honestly.
- Never hallucinate legal facts. If uncertain, say "I'm not sure about this — I recommend consulting an immigration attorney."
- For topics involving denial, removal, deportation, asylum, court proceedings, or appeals — always recommend consulting an attorney. These are too complex and high-stakes for general information.
- End every response that touches the user's specific situation with: "This is general information, not legal advice. For your specific situation, consider consulting an immigration attorney."

CONTEXT FROM IMMIGRATION KNOWLEDGE BASE:
{rag_context if rag_context else "No specific context available for this query."}"""


async def stream_chat(
    message: str,
    history: list[dict],
    system_prompt: str,
    model: str,
):
    """Stream a chat response from OpenRouter."""
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-10:])  # Last 10 messages for context window
    messages.append({"role": "user", "content": message})

    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        max_tokens=1024,
        temperature=0.3,
    )

    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
