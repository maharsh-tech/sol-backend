import httpx
from app.core.config import OPENROUTER_API_KEY, MODEL_NAME

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


async def generate_answer(system_prompt: str, user_message: str) -> str:
    """Send a chat completion request to OpenRouter and return the assistant reply."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "CompanyOS Knowledge Brain",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
