import uuid
import chromadb
from chromadb.config import Settings
from app.core.config import CHROMA_DB_PATH

_client: chromadb.ClientAPI | None = None
COLLECTION_NAME = "knowledge_brain"


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection() -> chromadb.Collection:
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> int:
    """Add text chunks with embeddings and metadata to ChromaDB. Returns count added."""
    collection = get_collection()
    ids = [str(uuid.uuid4()) for _ in texts]
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(ids)


def query_chunks(
    query_embedding: list[float],
    top_k: int = 5,
) -> dict:
    """Query ChromaDB for the top-k most similar chunks."""
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    return results
