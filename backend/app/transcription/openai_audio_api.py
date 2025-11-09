from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None

from ..logger import logger
from ..pipeline.interfaces import TranscriptionService
from .utils import extract_audio_from_media


@dataclass
class OpenAIAudioTranscriptionService(TranscriptionService):
    """Transcribe audio using OpenAI's hosted Audio API (Whisper / GPT-based)."""

    model: str = "gpt-4o-mini-transcribe"
    response_format: str = "text"
    temperature: float = 0.0

    def _client(self):
        if OpenAI is None:
            raise ImportError("openai package not installed. Install with `pip install openai`.")
        return OpenAI()

    def transcribe(self, video_path: str, job_id: str) -> str:
        audio_path = extract_audio_from_media(video_path, job_id, format="mp3")
        logger.log_step(job_id, "TRANSCRIPTION_OPENAI_AUDIO", f"Requesting transcription with model '{self.model}'")
        client = self._client()
        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                response_format=self.response_format,
                temperature=self.temperature,
            )

        text = transcription if isinstance(transcription, str) else transcription.get("text", "")
        logger.log_step(job_id, "TRANSCRIPTION_COMPLETE", f"OpenAI Audio API produced {len(text)} characters")
        return text.strip()
