from openai import AsyncOpenAI
from pinecone import Pinecone
from app.config import settings

# Embedding client — uses OpenRouter to proxy text-embedding-3-small
embedding_client = AsyncOpenAI(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
)

# Pinecone client
pc = None
index = None


def get_index():
    global pc, index
    if index is None and settings.pinecone_api_key:
        try:
            pc = Pinecone(api_key=settings.pinecone_api_key)
            index = pc.Index(settings.pinecone_index_name)
        except Exception as e:
            print(f"Pinecone initialization failed: {e}")
            return None
    return index


async def get_embedding(text: str) -> list[float]:
    """Get embedding vector for text. Uses OpenRouter's embedding endpoint."""
    try:
        response = await embedding_client.embeddings.create(
            model="openai/text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception:
        # If embedding fails, return empty — chat will work without RAG
        return []


async def retrieve_context(
    query: str,
    visa_type: str = "",
    top_k: int = 5,
) -> str:
    """Retrieve relevant immigration knowledge from Pinecone."""
    idx = get_index()
    if idx is None:
        return ""

    embedding = await get_embedding(query)
    if not embedding:
        return ""

    # Build metadata filter for visa type
    filter_dict = {}
    if visa_type:
        filter_dict["visa_types"] = {"$in": [visa_type]}

    try:
        results = idx.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if filter_dict else None,
        )

        chunks = []
        for match in results.matches:
            if match.score > 0.45:  # Include results with meaningful similarity
                meta = match.metadata or {}
                source = meta.get("source", "Unknown")
                title = meta.get("document_title", "")
                text = meta.get("text", "")
                chunks.append(f"[Source: {source} — {title}]\n{text}")

        return "\n\n---\n\n".join(chunks) if chunks else ""
    except Exception:
        return ""
