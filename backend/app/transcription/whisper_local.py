from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import whisper  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    whisper = None

from ..logger import logger
from ..pipeline.interfaces import TranscriptionService
from .utils import extract_audio_from_media


@dataclass
class WhisperLocalTranscriptionService(TranscriptionService):
    """Transcribe audio using the open-source Whisper model (runs locally)."""

    model_name: str = "base"
    language: Optional[str] = None
    temperature: float = 0.0

    def _load_model(self):
        if whisper is None:
            raise ImportError(
                "whisper library not installed. Install with `pip install openai-whisper`."
            )
        return whisper.load_model(self.model_name)

    def transcribe(self, video_path: str, job_id: str) -> str:
        audio_path = extract_audio_from_media(video_path, job_id, format="wav")
        logger.log_step(job_id, "TRANSCRIPTION_WHISPER_LOCAL", f"Using Whisper model '{self.model_name}'")
        model = self._load_model()
        result = model.transcribe(
            audio_path,
            language=self.language,
            temperature=self.temperature,
        )
        text = result.get("text", "").strip()
        logger.log_step(job_id, "TRANSCRIPTION_COMPLETE", f"Whisper (local) produced {len(text)} characters")
        return text
