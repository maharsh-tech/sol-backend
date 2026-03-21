# Knowledge Brain — Backend

RAG-powered document Q&A system. Upload PDF, Excel, or PowerPoint files and ask questions — answers are generated strictly from your documents with structured citations.

## Tech Stack
- **API**: FastAPI
- **Vector DB**: ChromaDB (local, persistent)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: OpenRouter API (any model, default: openai/gpt-oss-120b:free)
- **Parsers**: PyMuPDF (PDF), openpyxl (Excel), python-pptx (PowerPoint)

## Quick Start
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# Set OPENROUTER_API_KEY in .env
uvicorn app.main:app --reload --port 8000
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Service status |
| POST | /upload | Upload & index documents |
| POST | /ask | Ask a question |

## Documentation
See `DOCUMENTATION_INDEX.md` for the full list of docs.

## License
Internal — CompanyOS
