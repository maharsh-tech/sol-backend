"""Meeting intelligence: send transcript to OpenRouter and return structured analysis."""
import json
import logging
import re

from app.llm.openrouter_client import generate_answer

logger = logging.getLogger(__name__)

MEETING_SYSTEM_PROMPT = """You are an expert meeting analyst. Analyse the provided meeting transcript and return ONLY a valid JSON object — no extra text, no markdown fences.

The JSON must use EXACTLY this structure:
{
  "summary": "3-5 sentence paragraph summarising the entire meeting",
  "actionItems": [
    {
      "task": "clear action description",
      "owner": "person name or Unassigned",
      "deadline": "deadline string or Not specified",
      "priority": "High | Medium | Low"
    }
  ],
  "keyDecisions": ["decision 1", "decision 2"]
}

Rules:
- Identify speakers from labels like "Speaker 0:", "Speaker 1:", etc.
- Assign owners of action items to the speaker who committed to doing the work.
- Infer deadlines from phrases like "by Friday", "next week", "end of month".
- Extract only clear, actionable items.
- Keep summary concise (3–5 lines).
- Return ONLY the JSON object.
"""


def _extract_json(text: str) -> dict:
    """Try to extract a JSON object from an LLM response that may contain markdown fencing."""
    text = text.strip()
    # Strip markdown fences if present
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()
    return json.loads(text)


def analyse_transcript(transcript: str) -> dict:
    """
    Sends the transcript to OpenRouter and returns a parsed dict with:
      summary, actionItems, keyDecisions
    """
    raw = generate_answer(MEETING_SYSTEM_PROMPT, transcript)
    logger.info("OpenRouter meeting analysis response received")

    try:
        data = _extract_json(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Failed to parse OpenRouter JSON response: %s", exc)
        raise RuntimeError(
            f"AI analysis returned invalid JSON. Raw response: {raw[:300]}"
        ) from exc

    # Normalise keys in case LLM used alternate casing
    result = {
        "summary": data.get("summary", ""),
        "actionItems": data.get("actionItems", data.get("action_items", [])),
        "keyDecisions": data.get("keyDecisions", data.get("key_decisions", [])),
    }
    return result
