"""
Semantic FAQ Cache with frequency-based promotion.

Architecture:
  - TEMP TRACKER: A second ChromaDB collection that tracks query frequency.
    Persists across server restarts (unlike in-memory).
    Queries only get promoted to the FAQ cache after reaching the frequency threshold.
  - FAQ CACHE: ChromaDB collection storing only proven, frequently asked Q&A pairs.

This avoids cache pollution from one-off queries and ensures only genuinely
repeated questions consume permanent cache storage.
"""

import uuid
import logging
from datetime import datetime, timezone

from app.vectorstore.store import _get_client
from app.core.config import (
    FAQ_CACHE_COLLECTION,
    FAQ_SIMILARITY_THRESHOLD,
    FAQ_CACHE_TOP_K,
    FAQ_CACHE_TTL_DAYS,
    FAQ_FREQUENCY_THRESHOLD,
)

logger = logging.getLogger(__name__)

TEMP_TRACKER_COLLECTION = "faq_temp_tracker"


# ── ChromaDB collection helpers ───────────────────────────────────────────

def get_faq_collection():
    """Get or create the permanent FAQ cache collection."""
    client = _get_client()
    return client.get_or_create_collection(
        name=FAQ_CACHE_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def _get_temp_collection():
    """Get or create the temp frequency-tracker collection (persistent)."""
    client = _get_client()
    return client.get_or_create_collection(
        name=TEMP_TRACKER_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


# ── FAQ Cache (ChromaDB) lookup ────────────────────────────────────────────

def search_cache(query_embedding: list[float], threshold: float = FAQ_SIMILARITY_THRESHOLD):
    """
    Search the permanent FAQ cache for a similar question.
    Returns dict {id, question, answer} on hit, or None on miss.
    """
    try:
        collection = get_faq_collection()

        if collection.count() == 0:
            return None

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=FAQ_CACHE_TOP_K,
            include=["documents", "metadatas", "distances"],
        )

        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        ids = results.get("ids", [[]])[0]

        if not distances:
            return None

        best_distance = distances[0]
        similarity = 1.0 - best_distance

        if similarity >= threshold:
            meta = metadatas[0]
            # TTL check
            stored_ts = meta.get("timestamp", "")
            if stored_ts and FAQ_CACHE_TTL_DAYS > 0:
                try:
                    stored_dt = datetime.fromisoformat(stored_ts)
                    age_days = (datetime.now(timezone.utc) - stored_dt).days
                    if age_days > FAQ_CACHE_TTL_DAYS:
                        logger.info("FAQ cache entry expired (age=%d days), skipping", age_days)
                        return None
                except ValueError:
                    pass

            logger.info(
                "Cache Hit (FAQ) -- similarity=%.4f (threshold=%.2f)",
                similarity, threshold,
            )
            return {
                "id": ids[0],
                "question": meta.get("question", ""),
                "answer": meta.get("answer", ""),
            }

        logger.info(
            "Cache Miss -- best FAQ similarity=%.4f < threshold=%.2f",
            similarity, threshold,
        )
        return None

    except Exception as exc:
        logger.warning("FAQ cache search failed, falling back to RAG: %s", exc)
        return None


# ── Temp Tracker: frequency tracking + promotion ──────────────────────────

def track_in_temp_cache(question: str, answer: str, query_embedding: list[float]):
    """
    Track a query in the persistent temp-tracker collection.

    - If a similar query exists (similarity >= threshold): increment frequency,
      update the stored answer to the latest one.
    - If frequency reaches the threshold: promote to permanent FAQ cache and
      remove from temp tracker.
    - If no similar query exists: create a new entry (freq=1).

    All operations are wrapped in try/except so failures never break the response.
    """
    try:
        temp_col = _get_temp_collection()

        # Search for an existing similar entry in temp tracker
        match_id = None
        match_meta = None

        if temp_col.count() > 0:
            results = temp_col.query(
                query_embeddings=[query_embedding],
                n_results=1,
                include=["metadatas", "distances"],
            )

            distances = results.get("distances", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            ids = results.get("ids", [[]])[0]

            if distances and (1.0 - distances[0]) >= FAQ_SIMILARITY_THRESHOLD:
                match_id = ids[0]
                match_meta = metadatas[0]

        if match_id and match_meta:
            # Similar query found -- increment frequency
            new_freq = int(match_meta.get("frequency", 1)) + 1
            match_meta["frequency"] = new_freq
            match_meta["answer"] = answer
            match_meta["last_updated"] = datetime.now(timezone.utc).isoformat()

            logger.info(
                "Temp tracker frequency -> %d for: %s",
                new_freq, match_meta.get("question", "")[:80],
            )

            if new_freq >= FAQ_FREQUENCY_THRESHOLD:
                # Promote to permanent FAQ cache
                _promote_to_faq_cache(match_meta, query_embedding)
                # Remove from temp tracker
                temp_col.delete(ids=[match_id])
                logger.info("Removed promoted entry from temp tracker")
            else:
                # Just update the metadata
                temp_col.update(ids=[match_id], metadatas=[match_meta])
        else:
            # Brand new query -- add to temp tracker
            doc_id = str(uuid.uuid4())
            temp_col.add(
                ids=[doc_id],
                embeddings=[query_embedding],
                documents=[question],
                metadatas=[{
                    "question": question,
                    "answer": answer,
                    "frequency": 1,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                }],
            )
            logger.info("Temp tracker new entry (freq=1): %s", question[:80])

    except Exception as exc:
        logger.warning("Temp cache tracking failed (non-blocking): %s", exc)


def _promote_to_faq_cache(entry: dict, embedding: list[float]):
    """Promote a high-frequency entry into the permanent ChromaDB FAQ cache."""
    try:
        collection = get_faq_collection()
        doc_id = str(uuid.uuid4())
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[entry["question"]],
            metadatas=[{
                "question": entry["question"],
                "answer": entry["answer"],
                "frequency": int(entry.get("frequency", FAQ_FREQUENCY_THRESHOLD)),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        )
        logger.info(
            "Promoted to FAQ -- freq=%d, question=%s",
            entry.get("frequency", 0), entry["question"][:80],
        )
    except Exception as exc:
        logger.warning("FAQ promotion failed (non-blocking): %s", exc)


# ── Increment frequency (for existing FAQ cache hits) ─────────────────────

def increment_frequency(doc_id: str):
    """Increment the reuse counter for a cached FAQ entry."""
    try:
        collection = get_faq_collection()
        existing = collection.get(ids=[doc_id], include=["metadatas"])
        if existing and existing["metadatas"]:
            meta = existing["metadatas"][0]
            meta["frequency"] = int(meta.get("frequency", 1)) + 1
            collection.update(ids=[doc_id], metadatas=[meta])
    except Exception as exc:
        logger.warning("FAQ frequency increment failed (non-blocking): %s", exc)


# ── Popular questions ──────────────────────────────────────────────────────

def get_popular_questions(limit: int = 5) -> list[dict]:
    """Return the most frequently reused cached questions."""
    try:
        collection = get_faq_collection()
        count = collection.count()
        if count == 0:
            return []

        all_entries = collection.get(
            include=["metadatas"],
            limit=min(count, 200),
        )

        items = []
        for meta in all_entries.get("metadatas", []):
            items.append({
                "question": meta.get("question", ""),
                "frequency": int(meta.get("frequency", 1)),
            })

        items.sort(key=lambda x: x["frequency"], reverse=True)
        return items[:limit]

    except Exception as exc:
        logger.warning("Failed to fetch popular questions: %s", exc)
        return []
