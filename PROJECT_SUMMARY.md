# Project Summary

## What is AskOrg AI Backend?
The core API powering two major features: **Feature 1: Knowledge Brain** (RAG) and **Feature 2: Meeting Intelligence** (Audio Analysis).

## What it Does
**Knowledge Brain:**
1. Parses, chunks, and embeds uploaded documents (PDF, Excel, PPTX) into ChromaDB.
2. Retrieves relevant chunks and generates answers using OpenRouter LLMs.

**Meeting Intelligence:**
1. Accepts raw audio files and transcribes them using the Deepgram API.
2. Analyses transcripts to generate Executive Summaries, Action Items, and Key Decisions.
3. Automatically posts meeting briefs to a designated Slack channel.

## Architecture
- **Backend**: FastAPI REST API (this project)
- **Frontend**: React + Vite + Tailwind (separate project)
- **Vector DB**: ChromaDB (local, persistent)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: OpenRouter API (default: openai/gpt-oss-120b:free)

## Key Design Decisions
- **No Ollama** — uses OpenRouter for LLM access (cloud-only dependency)
- **Synchronous LLM calls** — uses `requests` library per project standard
- **Modular parsers** — each file type has its own parser module
- **Overlapping chunks** — 500 chars with 50 char overlap for better retrieval
- **Cosine similarity** — ChromaDB configured for cosine distance

## RAG Prompt
The system prompt instructs the LLM to answer ONLY from the provided context. If the answer isn't in the documents, it responds: "Answer not found in the provided documents."
