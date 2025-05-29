"""Voice generation module using ElevenLabs API."""

import os
import requests


def generate_voice(script: str, voice_id: str = "Rachel") -> str:
    """Generate an audio file from the script using ElevenLabs API."""
    headers = {
        "xi-api-key": os.getenv("ELEVEN_API_KEY"),
        "Content-Type": "application/json",
    }
    payload = {
        "text": script,
        "voice_settings": {"stability": 0.7, "similarity_boost": 0.8},
    }
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
        headers=headers,
        json=payload,
    )
    with open("voice.mp3", "wb") as f:
        f.write(response.content)
    return "voice.mp3"
