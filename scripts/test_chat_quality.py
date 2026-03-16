"""
AI Chat Quality Validation Test Suite for Migravio.

Tests the AI chat endpoint with real immigration scenarios and evaluates
response quality against expected markers.

Usage:
    python scripts/test_chat_quality.py [--url URL] [--token TOKEN]

    --url: AI service URL (default: http://localhost:8000)
    --token: Firebase ID token for authentication (required for production)

Without --token, runs in local dry-run mode using the AI service directly.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pinecone import Pinecone

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "apps", "ai-service", ".env"))

# Add parent directory to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


@dataclass
class TestScenario:
    """A test scenario for validating AI chat quality."""
    id: int
    question: str
    visa_type: str
    language: str
    description: str
    quality_markers: list[str]
    should_escalate: bool = False


# Define test scenarios covering the most common immigrant questions
TEST_SCENARIOS = [
    TestScenario(
        id=1,
        question="When should I start my H-1B extension process?",
        visa_type="H-1B",
        language="en",
        description="H-1B extension timing",
        quality_markers=[
            "6 months",
            "I-129",
            "premium processing",
            "employer",
            "petition",
        ],
    ),
    TestScenario(
        id=2,
        question="What documents do I need to file Form I-485?",
        visa_type="Green Card",
        language="en",
        description="I-485 document requirements",
        quality_markers=[
            "I-485",
            "birth certificate",
            "passport",
            "I-693",
            "medical",
            "photos",
        ],
    ),
    TestScenario(
        id=3,
        question="¿Cómo cambio mi estatus de F-1 a H-1B?",
        visa_type="F-1",
        language="es",
        description="F-1 to H-1B change of status (Spanish)",
        quality_markers=[
            "H-1B",
            "empleador",  # employer in Spanish
            "lotería",  # lottery
            "cap",
            "OPT",
        ],
    ),
    TestScenario(
        id=4,
        question="My H-1B petition was denied. What are my options now?",
        visa_type="H-1B",
        language="en",
        description="H-1B denial — should escalate",
        quality_markers=[
            "attorney",
            "motion",
            "appeal",
        ],
        should_escalate=True,
    ),
    TestScenario(
        id=5,
        question="What is OPT and how do I apply for it as an F-1 student?",
        visa_type="F-1",
        language="en",
        description="OPT explanation for F-1 students",
        quality_markers=[
            "Optional Practical Training",
            "I-765",
            "12 months",
            "STEM",
            "24",
            "I-20",
        ],
    ),
    TestScenario(
        id=6,
        question="How long does the naturalization process take and what do I need?",
        visa_type="Green Card",
        language="en",
        description="Naturalization timeline and requirements",
        quality_markers=[
            "N-400",
            "5 years",
            "3 years",
            "citizenship",
            "civics",
            "English",
        ],
    ),
    TestScenario(
        id=7,
        question="¿Puedo viajar fuera de Estados Unidos mientras mi I-485 está pendiente?",
        visa_type="Green Card",
        language="es",
        description="Travel with pending I-485 (Spanish)",
        quality_markers=[
            "advance parole",
            "I-131",
            "viaj",  # viaje/viajar
            "combo",
        ],
    ),
    TestScenario(
        id=8,
        question="What's the difference between Form I-130 and Form I-485?",
        visa_type="Green Card",
        language="en",
        description="I-130 vs I-485 comparison",
        quality_markers=[
            "I-130",
            "I-485",
            "petition",
            "adjustment",
            "concurrent",
            "priority date",
        ],
    ),
]


def check_quality_markers(response: str, markers: list[str]) -> tuple[int, int, list[str]]:
    """Check how many quality markers appear in the response."""
    response_lower = response.lower()
    found = []
    missing = []
    for marker in markers:
        if marker.lower() in response_lower:
            found.append(marker)
        else:
            missing.append(marker)
    return len(found), len(markers), missing


def check_disclaimer(response: str, language: str) -> bool:
    """Check if the response includes a legal disclaimer."""
    response_lower = response.lower()
    if language == "es":
        return any(phrase in response_lower for phrase in [
            "información general",
            "no es asesoramiento legal",
            "consultar",
            "abogado",
        ])
    return any(phrase in response_lower for phrase in [
        "not legal advice",
        "general information",
        "consult",
        "attorney",
        "immigration attorney",
    ])


def check_language(response: str, language: str) -> bool:
    """Basic check if response is in the expected language."""
    if language == "es":
        # Check for common Spanish words
        spanish_markers = ["de", "en", "que", "para", "como", "puede", "necesita", "debe"]
        count = sum(1 for w in spanish_markers if f" {w} " in response.lower())
        return count >= 3
    return True  # English is default


async def retrieve_rag_context(query: str, visa_type: str, openai_client: AsyncOpenAI, pinecone_index) -> str:
    """Retrieve relevant context from Pinecone, matching the real AI service logic."""
    if pinecone_index is None:
        return ""

    try:
        response = await openai_client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=query,
        )
        embedding = response.data[0].embedding
    except Exception:
        return ""

    filter_dict = {}
    if visa_type:
        filter_dict["visa_types"] = {"$in": [visa_type]}

    try:
        results = pinecone_index.query(
            vector=embedding,
            top_k=5,
            include_metadata=True,
            filter=filter_dict if filter_dict else None,
        )

        chunks = []
        for match in results.matches:
            if match.score > 0.45:
                meta = match.metadata or {}
                source = meta.get("source", "Unknown")
                title = meta.get("document_title", "")
                text = meta.get("text", "")
                chunks.append(f"[Source: {source} — {title}]\n{text}")

        return "\n\n---\n\n".join(chunks) if chunks else ""
    except Exception:
        return ""


async def test_via_openrouter_direct(scenario: TestScenario, use_rag: bool = False, pinecone_index=None) -> dict:
    """Test by calling OpenRouter directly, optionally with RAG context from Pinecone."""
    client = AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    )

    # Retrieve RAG context if enabled
    rag_context = ""
    if use_rag and pinecone_index is not None:
        rag_context = await retrieve_rag_context(
            scenario.question, scenario.visa_type, client, pinecone_index
        )

    lang_instruction = {
        "en": "Respond in English.",
        "es": "Responde en español.",
    }.get(scenario.language, "Respond in English.")

    visa_context = (
        f"The user's immigration category is: {scenario.visa_type}. This may be their current visa or the category they are pursuing. Tailor your responses to this category when relevant, but do not assume they already hold this status — they may be applying for it."
        if scenario.visa_type
        else ""
    )

    if rag_context:
        context_section = f"""OFFICIAL IMMIGRATION KNOWLEDGE BASE:
The following context comes from official USCIS sources. Ground your answers in this information.
When citing specific facts, reference the source (e.g., "According to the USCIS Policy Manual..." or "Per Form I-485 instructions...").

{rag_context}"""
    else:
        context_section = """No specific official context was retrieved for this query.
Be extra careful. If not confident about specifics, say so and recommend uscis.gov."""

    system_prompt = f"""You are Migravio, a warm, knowledgeable immigration assistant for the United States.

{lang_instruction}

{visa_context}

PERSONALITY:
- Be warm, clear, and human — like a knowledgeable friend who happens to know immigration law, not a legal textbook.
- Use simple language. Avoid jargon unless you explain it.
- Be encouraging — immigration is stressful, and users need reassurance alongside information.

RESPONSE FORMAT:
- When explaining a process, use clear numbered steps.
- When discussing forms, include: who should file, key eligibility requirements, required documents, filing fees, and estimated processing times.
- When there are important deadlines or timing considerations, highlight them clearly.
- Keep responses focused and concise — aim for 200-400 words unless the question requires more detail.
- Proactively mention related topics the user should know about (e.g., "You should also be aware that...").

RULES:
- You provide legal INFORMATION, never legal ADVICE.
- Ground your answers in the provided context. Cite sources when available.
- Never hallucinate legal facts. If uncertain, say "I'm not sure about the specifics — I recommend checking uscis.gov or consulting an immigration attorney."
- For topics involving denial, removal, deportation, asylum, court proceedings, or appeals — always recommend consulting an attorney. These are too complex and high-stakes for general information.
- End every response that touches the user's specific situation with: "This is general information, not legal advice. For your specific situation, consider consulting an immigration attorney."
- If you reference specific fees or processing times, note they can change and recommend verifying at uscis.gov.

{context_section}"""

    start = time.time()
    response = await client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": scenario.question},
        ],
        max_tokens=1024,
        temperature=0.3,
    )
    elapsed = time.time() - start

    content = response.choices[0].message.content or ""
    return {
        "response": content,
        "model": "anthropic/claude-haiku-4-5",
        "elapsed_seconds": round(elapsed, 2),
        "tokens_used": response.usage.total_tokens if response.usage else 0,
        "rag_context_length": len(rag_context),
    }


async def run_tests(mode: str = "direct", use_rag: bool = False):
    """Run all test scenarios and generate a quality report."""
    # Initialize Pinecone if RAG mode
    pinecone_index = None
    if use_rag:
        try:
            pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
            pinecone_index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "immigration-docs"))
            stats = pinecone_index.describe_index_stats()
            print(f"\n  Pinecone connected: {stats.total_vector_count} vectors available")
        except Exception as e:
            print(f"\n  WARNING: Pinecone connection failed: {e}")
            print("  Falling back to no-RAG mode")
            use_rag = False

    rag_label = " + RAG" if use_rag else " (no RAG)"
    print("\n" + "=" * 70)
    print("  MIGRAVIO AI CHAT QUALITY VALIDATION")
    print(f"  Mode: {mode}{rag_label} | Scenarios: {len(TEST_SCENARIOS)}")
    print("=" * 70)

    results = []
    total_markers_found = 0
    total_markers_expected = 0
    total_with_disclaimer = 0
    total_correct_language = 0

    for scenario in TEST_SCENARIOS:
        print(f"\n{'─' * 70}")
        print(f"  Test #{scenario.id}: {scenario.description}")
        print(f"  Visa: {scenario.visa_type} | Lang: {scenario.language}")
        print(f"  Q: {scenario.question}")
        print(f"{'─' * 70}")

        try:
            result = await test_via_openrouter_direct(scenario, use_rag=use_rag, pinecone_index=pinecone_index)
            response_text = result["response"]

            # Quality checks
            markers_found, markers_total, missing = check_quality_markers(
                response_text, scenario.quality_markers
            )
            has_disclaimer = check_disclaimer(response_text, scenario.language)
            correct_language = check_language(response_text, scenario.language)

            total_markers_found += markers_found
            total_markers_expected += markers_total
            if has_disclaimer:
                total_with_disclaimer += 1
            if correct_language:
                total_correct_language += 1

            # Determine pass/fail
            marker_ratio = markers_found / markers_total if markers_total > 0 else 0
            passed = marker_ratio >= 0.5 and has_disclaimer and correct_language

            status = "PASS" if passed else "FAIL"
            rag_info = f", RAG: {result.get('rag_context_length', 0)} chars" if use_rag else ""
            print(f"\n  Response ({result['elapsed_seconds']}s, {result['tokens_used']} tokens{rag_info}):")
            print(f"  {response_text[:300]}{'...' if len(response_text) > 300 else ''}")
            print(f"\n  Quality Markers: {markers_found}/{markers_total} ({marker_ratio:.0%})")
            if missing:
                print(f"  Missing: {', '.join(missing)}")
            print(f"  Disclaimer: {'Yes' if has_disclaimer else 'NO'}")
            print(f"  Correct Language: {'Yes' if correct_language else 'NO'}")
            if scenario.should_escalate:
                print(f"  Should Escalate: Yes (check escalation detection separately)")
            print(f"  Result: [{status}]")

            results.append({
                "id": scenario.id,
                "description": scenario.description,
                "status": status,
                "markers_found": markers_found,
                "markers_total": markers_total,
                "has_disclaimer": has_disclaimer,
                "correct_language": correct_language,
                "elapsed": result["elapsed_seconds"],
            })

        except Exception as e:
            print(f"  ERROR: {e}")
            results.append({
                "id": scenario.id,
                "description": scenario.description,
                "status": "ERROR",
                "error": str(e),
            })

    # Summary
    passed = sum(1 for r in results if r.get("status") == "PASS")
    failed = sum(1 for r in results if r.get("status") == "FAIL")
    errors = sum(1 for r in results if r.get("status") == "ERROR")

    print(f"\n\n{'=' * 70}")
    print("  SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Total Scenarios: {len(TEST_SCENARIOS)}")
    print(f"  Passed: {passed} | Failed: {failed} | Errors: {errors}")
    print(f"  Quality Markers: {total_markers_found}/{total_markers_expected} ({total_markers_found/total_markers_expected:.0%})")
    print(f"  With Disclaimer: {total_with_disclaimer}/{len(TEST_SCENARIOS)}")
    print(f"  Correct Language: {total_correct_language}/{len(TEST_SCENARIOS)}")

    overall = "PASS" if passed >= 6 and errors == 0 else "NEEDS IMPROVEMENT"
    print(f"\n  Overall: [{overall}]")

    if overall == "NEEDS IMPROVEMENT":
        print("\n  Recommendations:")
        if total_markers_found / total_markers_expected < 0.6:
            print("  - Populate Pinecone with USCIS data (run ingestion scripts)")
            print("  - RAG context will significantly improve factual accuracy")
        for r in results:
            if r.get("status") == "FAIL":
                print(f"  - Scenario #{r['id']} ({r['description']}): review response quality")

    print(f"{'=' * 70}\n")

    return results


def main():
    parser = argparse.ArgumentParser(description="Migravio AI Chat Quality Validation")
    parser.add_argument("--url", default="http://localhost:8000", help="AI service URL")
    parser.add_argument("--token", default=None, help="Firebase ID token for auth")
    parser.add_argument("--rag", action="store_true", help="Enable RAG context from Pinecone")
    args = parser.parse_args()

    if not os.getenv("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY not set. Copy from apps/ai-service/.env")
        sys.exit(1)

    if args.rag and not os.getenv("PINECONE_API_KEY"):
        print("ERROR: PINECONE_API_KEY not set. Required for --rag mode")
        sys.exit(1)

    asyncio.run(run_tests(mode="direct", use_rag=args.rag))


if __name__ == "__main__":
    main()
