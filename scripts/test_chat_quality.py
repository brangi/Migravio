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
            "denied",
            "option",
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
    # New scenarios testing expanded knowledge base
    TestScenario(
        id=9,
        question="When will my EB-2 India priority date be current?",
        visa_type="EB-2",
        language="en",
        description="Visa Bulletin priority dates (EB-2 India)",
        quality_markers=[
            "visa bulletin",
            "priority date",
            "India",
            "backlog",
        ],
    ),
    TestScenario(
        id=10,
        question="How long will my I-485 take to process?",
        visa_type="Green Card",
        language="en",
        description="Processing times for I-485",
        quality_markers=[
            "I-485",
            "months",
            "processing",
            "service center",
        ],
    ),
    TestScenario(
        id=11,
        question="What is the prevailing wage for a software engineer on an H-1B?",
        visa_type="H-1B",
        language="en",
        description="DOL prevailing wage for H-1B",
        quality_markers=[
            "prevailing wage",
            "level",
            "DOL",
        ],
    ),
    TestScenario(
        id=12,
        question="¿Qué cambios recientes hay en las reglas de H-1B?",
        visa_type="H-1B",
        language="es",
        description="Recent H-1B rule changes (Spanish)",
        quality_markers=[
            "H-1B",
            "regla",
        ],
    ),
    # === NEW: Work visa expansion scenarios ===
    TestScenario(
        id=13,
        question="Can a Mexican citizen apply for a TN visa? What professions qualify?",
        visa_type="TN",
        language="en",
        description="TN visa for Mexican professionals",
        quality_markers=[
            "USMCA",
            "Mexico",
            "profession",
            "bachelor",
        ],
    ),
    TestScenario(
        id=14,
        question="What is the E-2 treaty investor visa and which Latin American countries qualify?",
        visa_type="E-2",
        language="en",
        description="E-2 treaty investor visa — Americas focus",
        quality_markers=[
            "E-2",
            "invest",
            "treaty",
            "Mexico",
        ],
    ),
    TestScenario(
        id=15,
        question="¿Cómo funciona la visa H-2A para trabajadores agrícolas?",
        visa_type="H-2A",
        language="es",
        description="H-2A agricultural worker visa (Spanish)",
        quality_markers=[
            "H-2A",
            "agrícol",
            "empleador",
            "temporal",
        ],
    ),
    # === NEW: Non-immigrant expansion ===
    TestScenario(
        id=16,
        question="What is the K-1 fiancé visa process and how long does it take?",
        visa_type="K-1",
        language="en",
        description="K-1 fiancé visa process",
        quality_markers=[
            "K-1",
            "I-129F",
            "90 day",
            "marry",
        ],
    ),
    TestScenario(
        id=17,
        question="Can I extend my B-1/B-2 tourist visa while in the United States?",
        visa_type="B-1/B-2",
        language="en",
        description="B-1/B-2 extension",
        quality_markers=[
            "I-539",
            "extend",
            "6 months",
        ],
    ),
    # === NEW: Immigrant / Green Card expansion ===
    TestScenario(
        id=18,
        question="How does the EB-5 investor visa work? What's the minimum investment?",
        visa_type="EB-5",
        language="en",
        description="EB-5 investor program",
        quality_markers=[
            "EB-5",
            "invest",
            "I-526",
            "regional center",
        ],
    ),
    TestScenario(
        id=19,
        question="What are the family-based green card categories and their wait times?",
        visa_type="Green Card",
        language="en",
        description="Family-based immigration categories",
        quality_markers=[
            "immediate relative",
            "preference",
            "F1",
            "priority date",
        ],
    ),
    TestScenario(
        id=20,
        question="¿Qué es la lotería de visas de diversidad y quién puede participar?",
        visa_type="DV Lottery",
        language="es",
        description="DV Lottery eligibility (Spanish)",
        quality_markers=[
            "diversidad",
            "50,000",
            "país",
        ],
    ),
    # === NEW: Humanitarian — HIGH PRIORITY ===
    TestScenario(
        id=21,
        question="What is TPS and which countries currently have it? I'm from Venezuela.",
        visa_type="TPS",
        language="en",
        description="TPS for Venezuela",
        quality_markers=[
            "Temporary Protected Status",
            "Venezuela",
            "EAD",
            "register",
        ],
    ),
    TestScenario(
        id=22,
        question="I was a victim of a crime in the US. Can I apply for a U visa?",
        visa_type="U Visa",
        language="en",
        description="U visa for crime victims",
        quality_markers=[
            "U visa",
            "I-918",
            "law enforcement",
            "certification",
            "attorney",
        ],
        should_escalate=True,
    ),
    TestScenario(
        id=23,
        question="¿Cómo puedo aplicar para asilo en Estados Unidos?",
        visa_type="Asylum",
        language="es",
        description="Asylum application process (Spanish)",
        quality_markers=[
            "asilo",
            "I-589",
            "un año",
            "abogado",
        ],
        should_escalate=True,
    ),
    TestScenario(
        id=24,
        question="What is DACA and can I still renew my status?",
        visa_type="DACA",
        language="en",
        description="DACA renewal status",
        quality_markers=[
            "DACA",
            "Deferred Action",
            "renew",
            "I-821D",
        ],
    ),
    TestScenario(
        id=25,
        question="My spouse is abusive. Can I apply for immigration relief without them knowing?",
        visa_type="VAWA",
        language="en",
        description="VAWA self-petition — should escalate",
        quality_markers=[
            "VAWA",
            "self-petition",
            "confidential",
            "attorney",
        ],
        should_escalate=True,
    ),
    # === NEW: Extended forms ===
    TestScenario(
        id=26,
        question="What is Form I-140 and who files it?",
        visa_type="Green Card",
        language="en",
        description="I-140 immigrant petition basics",
        quality_markers=[
            "I-140",
            "employer",
            "EB-1",
            "EB-2",
            "EB-3",
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
    """Check if the response includes a legal disclaimer or recommendation to verify."""
    response_lower = response.lower()
    if language == "es":
        return any(phrase in response_lower for phrase in [
            "información general",
            "no es asesoramiento legal",
            "consultar",
            "abogado",
            "asesoría legal",
            "consejo legal",
            "no constituye",
            "profesional de inmigración",
            "asesor",
            "uscis.gov",
            "consulta con",
            "recomend",
            "especialista",
        ])
    return any(phrase in response_lower for phrase in [
        "not legal advice",
        "general information",
        "consult",
        "attorney",
        "immigration attorney",
        "uscis.gov",
        "verify",
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

    overall = "PASS" if passed >= 20 and errors == 0 else "NEEDS IMPROVEMENT"
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
