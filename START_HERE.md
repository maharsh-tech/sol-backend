# Start Here — AskOrg AI Backend

## Prerequisites
- Python 3.10+
- OpenRouter API key (free tier works)

## 3 Steps to Run

1. Install dependencies:
   ```bash
   cd sol-backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Configure API key:
   - Open `.env`
   - Set `OPENROUTER_API_KEY=your_actual_key`

3. Start the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

Open http://localhost:8000/health to verify.

## Next
- See `QUICK_REFERENCE.md` for API usage
- See `FILE_STRUCTURE.md` for codebase overview
