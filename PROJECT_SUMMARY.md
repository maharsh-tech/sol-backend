# Project Summary

## What is Knowledge Brain?
Feature 1 of CompanyOS — a RAG (Retrieval-Augmented Generation) document Q&A system.

## What it Does
1. Users upload company documents (PDF, Excel, PowerPoint)
2. System parses, chunks, and embeds the content into a vector database
3. Users ask natural language questions
4. System retrieves relevant chunks and generates grounded answers
5. Every answer includes structured citations (document name, page, snippet)

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
