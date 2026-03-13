"""
Test script to validate RAG ingestion setup.

Verifies:
- Environment variables are set
- OpenRouter API key works
- Pinecone connection works
- Embedding generation works
- Text chunking works

Usage:
    python scripts/test_setup.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_env_vars():
    """Test that required environment variables are set."""
    print("=" * 60)
    print("Testing Environment Variables")
    print("=" * 60)

    required_vars = [
        "OPENROUTER_API_KEY",
        "PINECONE_API_KEY",
        "PINECONE_INDEX_NAME",
    ]

    all_present = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask API keys
            if "KEY" in var:
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
        else:
            print(f"✗ {var}: NOT SET")
            all_present = False

    print()
    if all_present:
        print("✓ All required environment variables are set")
        return True
    else:
        print("✗ Missing required environment variables")
        print("\nCreate a .env file in the project root with:")
        print("  OPENROUTER_API_KEY=your_key_here")
        print("  PINECONE_API_KEY=your_key_here")
        print("  PINECONE_INDEX_NAME=immigration-docs")
        return False


async def test_openrouter():
    """Test OpenRouter API connection and embedding generation."""
    print("=" * 60)
    print("Testing OpenRouter Connection")
    print("=" * 60)

    try:
        from openai import AsyncOpenAI

        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        print("Generating test embedding...")
        response = await client.embeddings.create(
            model="openai/text-embedding-3-small",
            input="This is a test sentence for immigration document embedding.",
        )

        embedding = response.data[0].embedding
        print(f"✓ Successfully generated embedding")
        print(f"  Embedding dimension: {len(embedding)}")
        print(f"  Expected dimension: 1536")

        if len(embedding) == 1536:
            print("✓ Embedding dimension is correct")
            return True
        else:
            print("✗ Embedding dimension mismatch")
            return False

    except Exception as e:
        print(f"✗ OpenRouter test failed: {e}")
        return False


async def test_pinecone():
    """Test Pinecone connection and index access."""
    print("\n" + "=" * 60)
    print("Testing Pinecone Connection")
    print("=" * 60)

    try:
        from pinecone import Pinecone

        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME", "immigration-docs")

        pc = Pinecone(api_key=api_key)
        print("✓ Pinecone client initialized")

        # List indexes
        indexes = pc.list_indexes()
        print(f"Available indexes: {[idx.name for idx in indexes]}")

        # Try to connect to the index
        index = pc.Index(index_name)
        print(f"✓ Connected to index '{index_name}'")

        # Get index stats
        stats = index.describe_index_stats()
        print(f"  Total vectors: {stats.total_vector_count}")
        print(f"  Index dimension: {stats.dimension}")

        if stats.dimension == 1536:
            print("✓ Index dimension matches embedding dimension (1536)")
            return True
        else:
            print(f"✗ Index dimension mismatch: expected 1536, got {stats.dimension}")
            print("\nYou may need to recreate the index with dimension=1536")
            return False

    except Exception as e:
        print(f"✗ Pinecone test failed: {e}")
        print("\nMake sure you've created a Pinecone index named 'immigration-docs'")
        print("with dimension=1536 and metric='cosine'")
        return False


async def test_chunking():
    """Test text chunking utility."""
    print("\n" + "=" * 60)
    print("Testing Text Chunking")
    print("=" * 60)

    try:
        from shared import chunk_text

        # Test text (roughly 1000 words)
        test_text = """
        Form I-485 is used to apply for lawful permanent resident status (green card)
        while in the United States. This is known as adjustment of status.
        Foreign nationals already in the U.S. who are eligible for an immigrant visa
        can use this form. This includes immediate relatives of U.S. citizens,
        family-sponsored preference category applicants, employment-based preference
        category applicants, diversity visa lottery winners, and refugees and asylees
        seeking to adjust status.

        To be eligible, you must be physically present in the United States,
        have an immigrant visa immediately available, be admissible to the United States,
        and not be in removal proceedings with some exceptions.

        Required documents include Form I-485 and all required supplements,
        copy of birth certificate with certified translation, copy of passport and visa,
        two passport-style photos, Form I-693 medical examination, Form I-864 affidavit
        of support if required, evidence of approved immigrant petition like I-140 or I-130,
        and copy of Employment Authorization Document if applicable.
        """ * 10  # Repeat to get more text

        chunks = chunk_text(test_text, chunk_size=512, overlap=50)

        print(f"Input text length: {len(test_text)} characters")
        print(f"Input word count: {len(test_text.split())} words")
        print(f"Generated chunks: {len(chunks)}")
        print(f"Average chunk size: {sum(len(c.split()) for c in chunks) / len(chunks):.0f} words")

        # Expected: ~384 words per chunk (512 tokens * 0.75)
        avg_chunk_words = sum(len(c.split()) for c in chunks) / len(chunks)

        if 300 <= avg_chunk_words <= 450:
            print("✓ Chunk sizes are within expected range (300-450 words)")
            print(f"\nSample chunk (first 200 chars):")
            print(f"  {chunks[0][:200]}...")
            return True
        else:
            print(f"✗ Chunk sizes outside expected range: {avg_chunk_words:.0f} words")
            return False

    except Exception as e:
        print(f"✗ Chunking test failed: {e}")
        return False


async def test_full_pipeline():
    """Test a minimal end-to-end ingestion pipeline."""
    print("\n" + "=" * 60)
    print("Testing Full Pipeline (Dry Run)")
    print("=" * 60)

    try:
        from shared import chunk_text, setup_clients, get_embedding

        # Initialize clients
        print("Initializing clients...")
        clients = await setup_clients()
        print("✓ Clients initialized")

        # Test content
        test_content = """
        The H-1B visa is a nonimmigrant visa that allows U.S. companies to employ
        foreign workers in specialty occupations. A specialty occupation requires
        the application of specialized knowledge and a bachelor's degree or the
        equivalent of work experience.
        """

        # Chunk the content
        chunks = chunk_text(test_content, chunk_size=512, overlap=50)
        print(f"✓ Created {len(chunks)} chunks")

        # Generate embedding for first chunk
        print("Generating embedding for test chunk...")
        embedding = await get_embedding(clients.openai_client, chunks[0])
        print(f"✓ Generated embedding (dimension: {len(embedding)})")

        # Create test metadata
        metadata = {
            "source": "test",
            "document_title": "Test Document",
            "section": "test_section",
            "visa_types": ["H-1B"],
            "text": chunks[0],
        }

        print("\nTest metadata structure:")
        for key, value in metadata.items():
            if key == "text":
                print(f"  {key}: {str(value)[:50]}...")
            else:
                print(f"  {key}: {value}")

        print("\n✓ Full pipeline test successful (dry run)")
        print("\nYou can now run the actual ingestion scripts:")
        print("  python scripts/ingest_forms.py")
        print("  python scripts/ingest_uscis_manual.py")

        return True

    except Exception as e:
        print(f"✗ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Migravio RAG Ingestion Setup Validation")
    print("=" * 60 + "\n")

    results = {}

    # Test environment variables
    results["env_vars"] = await test_env_vars()

    if not results["env_vars"]:
        print("\n✗ Setup incomplete: Fix environment variables first")
        sys.exit(1)

    # Test OpenRouter
    results["openrouter"] = await test_openrouter()

    # Test Pinecone
    results["pinecone"] = await test_pinecone()

    # Test chunking
    results["chunking"] = await test_chunking()

    # Test full pipeline if previous tests passed
    if all([results["openrouter"], results["pinecone"], results["chunking"]]):
        results["pipeline"] = await test_full_pipeline()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All tests passed! Setup is ready.")
        print("\nNext steps:")
        print("  1. python scripts/ingest_forms.py")
        print("  2. python scripts/ingest_uscis_manual.py --volumes 2,3,5,7")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
