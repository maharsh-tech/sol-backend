import requests
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_answer(system_prompt: str, user_message: str) -> str:
    """Send a chat completion request to OpenRouter and return the assistant reply."""
    response = requests.post(
        url=OPENROUTER_API_URL,
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "HTTP-Referer": "http://localhost:3000",
            "X-OpenRouter-Title": "CompanyOS",
        },
        data=json.dumps({
            "model": os.getenv("MODEL_NAME", "nvidia/nemotron-3-super-120b-a12b:free"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        }),
    )
    response.raise_for_status()
    result = response.json()
    answer = result["choices"][0]["message"]["content"]
    logging.info("OpenRouter response received successfully")
    return answer
