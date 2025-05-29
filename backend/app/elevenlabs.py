"""Voice generation module using ElevenLabs API."""

from envloader import ELEVEN_API_KEY as ELEVENLABS_API_KEY


def generate_voice(text: str) -> str:
    """Generate an audio file from text and return the audio path."""
    # TODO: integrate with ElevenLabs API using ELEVENLABS_API_KEY
    return "path/to/generated_audio.mp3"
