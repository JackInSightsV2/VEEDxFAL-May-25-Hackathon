"""Voice generation module using ElevenLabs API."""

import os
import requests
from .logger import logger


def generate_voice(script: str, job_id: str = None, voice_id: str = "Rachel") -> str:
    """Generate an audio file from the script using ElevenLabs API."""
    headers = {
        "xi-api-key": os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY"),
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
    
    # Save audio to job folder
    if job_id:
        audio_path = logger.get_job_file_path(job_id, "voice.mp3")
    else:
        audio_path = "voice.mp3"
    
    with open(audio_path, "wb") as f:
        f.write(response.content)
    return audio_path
