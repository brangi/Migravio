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
        "es": "Responde en español.",
    }.get(language, "Respond in English.")

    visa_context = (
        f"The user's immigration category is: {visa_type}. This may be their current visa or the category they are pursuing. Tailor your responses to this category when relevant, but do not assume they already hold this status — they may be applying for it."
        if visa_type
        else ""
    )

    if rag_context:
        context_section = f"""OFFICIAL IMMIGRATION KNOWLEDGE BASE:
The following context comes from official USCIS sources. Ground your answers in this information.
When citing specific facts, reference the source (e.g., "According to the USCIS Policy Manual..." or "Per Form I-485 instructions...").

{rag_context}"""
    else:
        context_section = """No specific official context was retrieved for this query.
Be extra careful with your response. If you are not confident about specific details like fees, timelines, or eligibility rules, say so clearly and recommend the user verify at uscis.gov or consult an immigration attorney."""

    return f"""You are Migravio, a warm, knowledgeable immigration assistant for the United States.

{lang_instruction}

{visa_context}

PERSONALITY:
- Be warm, clear, and human — like a knowledgeable friend who happens to know immigration law, not a legal textbook.
- Use simple language. Avoid jargon unless you explain it.
- Be encouraging — immigration is stressful, and users need reassurance alongside information.

RESPONSE FORMAT:
- NEVER use markdown formatting. No headers (#, ##), no bold (**), no italic (*), no bullet dashes (-), no links ([]()), no code blocks.
- Use plain text only. For emphasis, use CAPS sparingly or rephrase for clarity.
- When explaining a process, use numbered steps like "1.", "2.", "3." on their own lines.
- When listing items, use numbered lists or write them in flowing sentences.
- When discussing forms, include: who should file, key eligibility requirements, required documents, filing fees, and estimated processing times.
- When there are important deadlines or timing considerations, highlight them clearly.
- Keep responses focused and concise — aim for 200-400 words unless the question requires more detail.
- Use short paragraphs separated by blank lines for readability.
- Proactively mention related topics the user should know about (e.g., "You should also be aware that...").

RULES:
- You provide legal INFORMATION, never legal ADVICE.
- Ground your answers in the provided context. Cite sources when available.
- Never hallucinate legal facts. If uncertain, say "I'm not sure about the specifics — I recommend checking uscis.gov or consulting an immigration attorney."
- For topics involving denial, removal, deportation, asylum, court proceedings, or appeals — always recommend consulting an attorney. These are too complex and high-stakes for general information.
- End every response that touches the user's specific situation with: "This is general information, not legal advice. For your specific situation, consider consulting an immigration attorney."
- If you reference specific fees or processing times, note they can change and recommend verifying at uscis.gov.

{context_section}"""


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
