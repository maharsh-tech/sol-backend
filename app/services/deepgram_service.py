"""Deepgram transcription + speaker diarization service."""
import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

DEEPGRAM_API_URL = "https://api.deepgram.com/v1/listen"


def transcribe_audio(audio_bytes: bytes, mimetype: str = "audio/mpeg") -> str:
    """
    Send audio bytes to Deepgram and return a speaker-labelled transcript string.

    Returns text in the form:
        Speaker 0: Hello, how are you?
        Speaker 1: I am fine, thanks.
    """
    api_key = os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY is not set in environment variables.")

    params = {
        "model": "nova-2",
        "diarize": "true",
        "punctuate": "true",
        "utterances": "true",
        "smart_format": "true",
    }

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": mimetype,
    }

    response = requests.post(
        DEEPGRAM_API_URL,
        params=params,
        headers=headers,
        data=audio_bytes,
        timeout=120,
    )

    if response.status_code != 200:
        logger.error("Deepgram error %s: %s", response.status_code, response.text)
        raise RuntimeError(f"Deepgram transcription failed: {response.status_code} {response.text}")

    data = response.json()

    # Build a speaker-labelled transcript from utterances
    utterances = data.get("results", {}).get("utterances", [])
    if utterances:
        lines = []
        for utt in utterances:
            speaker = f"Speaker {utt.get('speaker', 0)}"
            text = utt.get("transcript", "").strip()
            if text:
                lines.append(f"{speaker}: {text}")
        return "\n".join(lines)

    # Fallback: plain transcript without diarization
    channels = data.get("results", {}).get("channels", [])
    if channels:
        plain = channels[0].get("alternatives", [{}])[0].get("transcript", "")
        return f"Speaker 0: {plain}"

    raise RuntimeError("Deepgram returned an empty transcript.")
