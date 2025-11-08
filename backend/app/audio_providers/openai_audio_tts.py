from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None

from ..logger import logger
from ..pipeline.interfaces import AudioService


@dataclass
class OpenAIUniversalAudioService(AudioService):
    """Generate speech using OpenAI's Audio (TTS) API."""

    model: str = "gpt-4o-mini-tts"
    voice: str = "alloy"
    format: str = "mp3"
    speaking_rate: Optional[float] = None

    def _client(self):
        if OpenAI is None:
            raise ImportError("openai package not installed. Install with `pip install openai`.")
        return OpenAI()

    def synthesize(self, text: str, job_id: str, *, gender: Optional[str]) -> str:
        client = self._client()
        logger.log_step(job_id, "AUDIO_GENERATION", f"Generating OpenAI TTS audio with model {self.model}")
        params = {
            "model": self.model,
            "voice": self.voice,
            "input": text,
            "format": self.format,
        }
        if self.speaking_rate:
            params["speaking_rate"] = self.speaking_rate
        response = client.audio.speech.create(**params)
        audio_bytes = response.read()

        audio_path = logger.get_job_file_path(job_id, f"openai_tts.{self.format}")
        with open(audio_path, "wb") as audio_file:
            audio_file.write(audio_bytes)
        logger.log_step(job_id, "AUDIO_GENERATION_SUCCESS", f"OpenAI TTS audio saved to {audio_path}")
        return audio_path
