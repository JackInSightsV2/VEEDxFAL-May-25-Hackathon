"""Voice generation module using ElevenLabs API."""

import os
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


def generate_voice(text: str) -> str:
    """Generate an audio file from text and return the audio path."""
    # TODO: integrate with ElevenLabs API using ELEVENLABS_API_KEY
    return "path/to/generated_audio.mp3"
