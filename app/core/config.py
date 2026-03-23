import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "openai/gpt-oss-120b:free")
CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")


EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 50

TOP_K: int = 5

UPLOAD_DIR: Path = Path("./uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS: set[str] = {".pdf", ".xlsx", ".pptx"}

# ── FAQ Semantic Cache ─────────────────────────────────────────────────────
FAQ_CACHE_COLLECTION: str = "faq_cache_collection"
FAQ_SIMILARITY_THRESHOLD: float = float(os.getenv("FAQ_SIMILARITY_THRESHOLD", "0.85"))
FAQ_CACHE_TOP_K: int = 1
FAQ_CACHE_TTL_DAYS: int = int(os.getenv("FAQ_CACHE_TTL_DAYS", "30"))
FAQ_FREQUENCY_THRESHOLD: int = int(os.getenv("FAQ_FREQUENCY_THRESHOLD", "3"))
FAQ_TEMP_CACHE_SIZE: int = int(os.getenv("FAQ_TEMP_CACHE_SIZE", "500"))
