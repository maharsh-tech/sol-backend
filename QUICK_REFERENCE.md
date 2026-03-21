# Quick Reference

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Upload Documents
```bash
curl -X POST http://localhost:8000/upload \
  -F "files=@report.pdf" \
  -F "files=@data.xlsx" \
  -F "files=@slides.pptx"
```
Response:
```json
{
  "message": "Documents processed and indexed successfully.",
  "documents": ["report.pdf", "data.xlsx", "slides.pptx"],
  "total_chunks": 42
}
```

### Ask a Question
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What are the key findings?\"}"
```
Response:
```json
{
  "answer": "The key findings include...",
  "citations": [
    {
      "document_name": "report.pdf",
      "page": 7,
      "snippet": "Our analysis reveals..."
    }
  ],
  "confidence": "high"
}
```

## Environment Variables
| Variable | Required | Default |
|----------|----------|---------|
| OPENROUTER_API_KEY | Yes | — |
| MODEL_NAME | No | openai/gpt-oss-120b:free |
| CHROMA_DB_PATH | No | ./chroma_db |

## Supported File Types
- PDF (.pdf)
- Excel (.xlsx)
- PowerPoint (.pptx)

## Confidence Levels
- **high** — 2+ strong matches found
- **medium** — 1 strong match found
- **low** — weak or no matches
