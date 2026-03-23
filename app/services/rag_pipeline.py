import logging

from app.embeddings.embedder import embed_query
from app.vectorstore.store import query_chunks
from app.llm.openrouter_client import generate_answer
from app.core.config import TOP_K
from app.services.faq_cache import search_cache, track_in_temp_cache, increment_frequency

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a precise document assistant. Answer the user's question using ONLY the context provided below. Do not use any external knowledge. If the answer is not present in the context, say exactly: "Answer not found in the provided documents."

Always be concise. Do NOT include any inline citation markers (like [1], 【1†source】, etc.) in your answer text. The system handles citations automatically.

Context:
{context}

Question:
{question}"""


def _build_context(documents: list[str], metadatas: list[dict]) -> str:
    """Build a context string from retrieved chunks."""
    parts: list[str] = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas), start=1):
        source = meta.get("document_name", "unknown")
        page = meta.get("page", "?")
        parts.append(f"[Source {i}: {source}, Page/Sheet {page}]\n{doc}")
    return "\n\n".join(parts)


def _compute_confidence(distances: list[float]) -> str:
    """Determine confidence level based on similarity distances.
    ChromaDB cosine distance: 0 = identical, 2 = opposite.
    """
    if not distances:
        return "low"
    strong = sum(1 for d in distances if d < 0.5)
    if strong >= 2:
        return "high"
    if strong >= 1:
        return "medium"
    return "low"


def ask_question(question: str) -> dict:
    """Full RAG pipeline with frequency-based smart cache.

    Flow:
    1. Embed the question
    2. Check FAQ cache (ChromaDB) for a semantically similar question
       -> if HIT: return cached answer (no LLM call)
    3. If MISS: run full RAG pipeline (retrieve chunks -> LLM)
    4. Track query in temp cache (frequency counter)
       -> if frequency >= threshold: promote to FAQ cache
    """
    # Step 1 -- Embed the question (used by cache, temp tracker, and RAG)
    query_embedding = embed_query(question)

    # Step 2 -- Check permanent FAQ cache (ChromaDB)
    cached = search_cache(query_embedding)
    if cached:
        increment_frequency(cached["id"])
        logger.info("Returning cached answer for: %s", question[:80])
        return {
            "answer": cached["answer"],
            "citations": [],
            "confidence": "high",
            "source": "cache",
        }

    # Step 3 -- Cache miss -> run existing RAG pipeline
    results = query_chunks(query_embedding, top_k=TOP_K)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "answer": "Answer not found in the provided documents.",
            "citations": [],
            "confidence": "low",
            "source": "rag",
        }

    context = _build_context(documents, metadatas)
    prompt = SYSTEM_PROMPT.format(context=context, question=question)

    answer = generate_answer(prompt, question)

    citations = []
    for doc, meta in zip(documents, metadatas):
        snippet = doc[:200].strip()
        citations.append(
            {
                "document_name": meta.get("document_name", "unknown"),
                "page": meta.get("page", "?"),
                "snippet": snippet,
            }
        )

    confidence = _compute_confidence(distances)

    # Step 4 -- Track in temp cache (promotes to FAQ at frequency >= threshold)
    track_in_temp_cache(question, answer, query_embedding)

    return {
        "answer": answer,
        "citations": citations,
        "confidence": confidence,
        "source": "rag",
    }
