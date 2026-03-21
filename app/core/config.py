import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "openai/gpt-oss-120b:free")
CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")

EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 50

TOP_K: int = 5

UPLOAD_DIR: Path = Path("./uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS: set[str] = {".pdf", ".xlsx", ".pptx"}
