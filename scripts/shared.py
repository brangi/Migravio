"""
Shared utilities for RAG ingestion scripts.

Provides chunking, embedding, and Pinecone upsert functionality
used by all Migravio ingestion scripts.
"""

import hashlib
import logging
import os
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pinecone import Pinecone

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class IngestionClients:
    """Container for OpenRouter and Pinecone clients."""

    def __init__(self):
        self.openai_client: AsyncOpenAI | None = None
        self.pinecone_client: Pinecone | None = None
        self.index = None

    async def setup(self):
        """Initialize OpenRouter and Pinecone clients from environment variables."""
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        openrouter_base_url = os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        )
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "immigration-docs")

        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")

        # Initialize OpenAI client pointed at OpenRouter
        self.openai_client = AsyncOpenAI(
            api_key=openrouter_api_key,
            base_url=openrouter_base_url,
        )
        logger.info("OpenRouter client initialized")

        # Initialize Pinecone client
        self.pinecone_client = Pinecone(api_key=pinecone_api_key)
        self.index = self.pinecone_client.Index(pinecone_index_name)
        logger.info(f"Pinecone index '{pinecone_index_name}' connected")


async def get_embedding(client: AsyncOpenAI, text: str) -> list[float]:
    """
    Get embedding vector for text using OpenRouter's embedding endpoint.

    Args:
        client: AsyncOpenAI client configured for OpenRouter
        text: Text to embed

    Returns:
        List of floats representing the embedding vector

    Raises:
        Exception: If embedding request fails
    """
    try:
        response = await client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}")
        raise


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks by approximate token count.

    Uses word-based approximation: ~0.75 words per token.
    - chunk_size=512 tokens ≈ 384 words
    - overlap=50 tokens ≈ 38 words

    Args:
        text: Text to chunk
        chunk_size: Target chunk size in tokens (default: 512)
        overlap: Overlap size in tokens (default: 50)

    Returns:
        List of text chunks with overlap
    """
    # Approximate tokens as words * 0.75
    words_per_chunk = int(chunk_size * 0.75)
    words_overlap = int(overlap * 0.75)

    # Split into words (preserving whitespace roughly)
    words = text.split()

    if len(words) <= words_per_chunk:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = start + words_per_chunk
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        # Move forward by (chunk_size - overlap)
        start += words_per_chunk - words_overlap

    return chunks


def generate_vector_id(source: str, section: str) -> str:
    """
    Generate deterministic vector ID based on source and section.

    This ensures re-running ingestion updates existing vectors
    rather than creating duplicates.

    Args:
        source: Source identifier (e.g., "uscis_manual", "form_i485")
        section: Section identifier (e.g., "volume_1_chapter_2")

    Returns:
        Deterministic hash-based ID string
    """
    content = f"{source}::{section}"
    hash_digest = hashlib.sha256(content.encode()).hexdigest()
    return f"{source}_{hash_digest[:16]}"


async def upsert_to_pinecone(
    index,
    chunks: list[str],
    metadata_list: list[dict[str, Any]],
    source: str,
    dry_run: bool = False,
) -> int:
    """
    Upsert text chunks to Pinecone with metadata.

    Batches vectors into groups of 100 for efficient upsert.
    Generates embeddings for each chunk and creates deterministic IDs.

    Args:
        index: Pinecone index instance
        chunks: List of text chunks to upsert
        metadata_list: List of metadata dicts (one per chunk)
        source: Source identifier for ID generation
        dry_run: If True, skip actual API calls and just log

    Returns:
        Number of vectors upserted

    Raises:
        ValueError: If chunks and metadata_list lengths don't match
    """
    if len(chunks) != len(metadata_list):
        raise ValueError(
            f"Chunks ({len(chunks)}) and metadata ({len(metadata_list)}) must have same length"
        )

    if dry_run:
        logger.info(f"[DRY RUN] Would upsert {len(chunks)} vectors to Pinecone")
        for i, (chunk, meta) in enumerate(zip(chunks[:3], metadata_list[:3])):
            logger.info(f"  Sample {i+1}: {meta.get('document_title', 'N/A')}")
            logger.info(f"    Text preview: {chunk[:100]}...")
        return len(chunks)

    # Get OpenRouter client from environment
    clients = IngestionClients()
    await clients.setup()

    vectors_to_upsert = []
    batch_size = 100

    for i, (chunk, metadata) in enumerate(zip(chunks, metadata_list)):
        # Generate embedding
        try:
            embedding = await get_embedding(clients.openai_client, chunk)
        except Exception as e:
            logger.error(f"Failed to embed chunk {i}: {e}")
            continue

        # Generate deterministic ID
        section_id = metadata.get("section", f"chunk_{i}")
        vector_id = generate_vector_id(source, section_id)

        # Add text to metadata
        metadata["text"] = chunk

        vectors_to_upsert.append(
            {
                "id": vector_id,
                "values": embedding,
                "metadata": metadata,
            }
        )

        # Upsert in batches of 100
        if len(vectors_to_upsert) >= batch_size:
            try:
                index.upsert(vectors=vectors_to_upsert)
                logger.info(
                    f"Upserted batch of {len(vectors_to_upsert)} vectors ({i+1}/{len(chunks)} total)"
                )
                vectors_to_upsert = []
            except Exception as e:
                logger.error(f"Failed to upsert batch: {e}")
                raise

    # Upsert remaining vectors
    if vectors_to_upsert:
        try:
            index.upsert(vectors=vectors_to_upsert)
            logger.info(
                f"Upserted final batch of {len(vectors_to_upsert)} vectors ({len(chunks)} total)"
            )
        except Exception as e:
            logger.error(f"Failed to upsert final batch: {e}")
            raise

    return len(chunks)


async def setup_clients() -> IngestionClients:
    """
    Initialize and return OpenRouter and Pinecone clients.

    Returns:
        IngestionClients instance with initialized clients

    Raises:
        ValueError: If required environment variables are missing
    """
    clients = IngestionClients()
    await clients.setup()
    return clients
