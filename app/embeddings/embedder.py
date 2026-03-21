from sentence_transformers import SentenceTransformer
from app.core.config import EMBEDDING_MODEL_NAME

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of text strings."""
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Generate an embedding for a single query string."""
    model = _get_model()
    embedding = model.encode([query], show_progress_bar=False)
    return embedding[0].tolist()
