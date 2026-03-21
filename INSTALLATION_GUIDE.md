# Installation Guide

## System Requirements
- Python 3.10 or higher
- pip (Python package manager)
- ~500 MB disk space (for sentence-transformers model download)
- Internet connection (for OpenRouter API calls and initial model download)

## Step-by-Step Installation

### 1. Create Virtual Environment
```bash
cd sol-backend
python -m venv venv
```

### 2. Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```
**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy the example and fill in your key:
```bash
copy .env.example .env
```
Edit `.env`:
```
OPENROUTER_API_KEY=sk-or-v1-your-actual-key
MODEL_NAME=openai/gpt-oss-120b:free
CHROMA_DB_PATH=./chroma_db
```

Get your free API key at: https://openrouter.ai/keys

### 5. Start the Server
```bash
uvicorn app.main:app --reload --port 8000
```

### 6. Verify
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"ok","service":"Knowledge Brain"}`

## Troubleshooting
- **ModuleNotFoundError**: Ensure your venv is activated
- **Connection refused**: Check the server is running on port 8000
- **OpenRouter 401**: Verify your API key in `.env`
