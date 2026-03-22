# AskOrg AI — Backend

Core API powering **Feature 1: Knowledge Brain** (RAG document Q&A) and **Feature 2: Meeting Intelligence** (Audio transcription, AI analysis, Slack integration).

## Tech Stack
- **API**: FastAPI
- **Vector DB**: ChromaDB (local, persistent)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: OpenRouter API (Default: Google Gemini 2.0 Flash Lite)
- **Audio**: Deepgram API (Speech-to-Text transcription)
- **Integrations**: Slack Incoming Webhooks
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
| Method | Endpoint          | Description |
|--------|-------------------|-------------|
| GET    | /health           | Service status |
| POST   | /upload           | Upload & index documents |
| POST   | /ask              | Ask a question against documents |
| POST   | /meeting/analyze  | Transcribe audio & generate meeting analysis |
| POST   | /meeting/slack    | Post meeting results to Slack |

## Documentation
See `DOCUMENTATION_INDEX.md` for the full list of docs.

## License
Internal — AskOrg AI
