from app.core.config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, metadata: dict) -> list[dict]:
    """Split text into overlapping chunks preserving the original metadata."""
    chunks: list[dict] = []
    if not text:
        return chunks
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        chunks.append(
            {
                "text": chunk.strip(),
                "metadata": {**metadata},
            }
        )
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if c["text"]]
