# File Structure

```
sol-backend/
├── .env                      # Environment variables (API key, model name)
├── .env.example              # Template for .env
├── .gitignore
├── requirements.txt          # Python dependencies
│
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry point + CORS
│   │
│   ├── core/
│   │   └── config.py         # All settings loaded from .env
│   │
│   ├── api/
│   │   └── routes.py         # /health, /upload, /ask endpoints
│   │
│   ├── parsers/
│   │   ├── pdf_parser.py     # PyMuPDF — extracts text per page
│   │   ├── excel_parser.py   # openpyxl — extracts text per sheet
│   │   └── pptx_parser.py    # python-pptx — extracts text per slide
│   │
│   ├── services/
│   │   ├── chunker.py              # Splits text into overlapping chunks
│   │   ├── rag_pipeline.py         # Full RAG: embed → retrieve → generate
│   │   ├── deepgram_service.py     # Transcribes meeting audio
│   │   ├── meeting_analysis_service.py # AI summary, action items, decisions 
│   │   └── slack_service.py        # Posts meeting briefs to Slack
│   │
│   ├── embeddings/
│   │   └── embedder.py       # sentence-transformers wrapper
│   │
│   ├── vectorstore/
│   │   └── store.py          # ChromaDB add/query operations
│   │
│   ├── llm/
│   │   └── openrouter_client.py  # OpenRouter API via requests
│   │
│   ├── schemas/
│   │   └── models.py         # Pydantic request/response models
│   │
│   └── utils/
│       └── (reserved for future utilities)
```
