from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:
    from google.cloud import speech  # type: ignore
except ImportError:  # pragma: no cover
    speech = None

from ..logger import logger
from ..pipeline.interfaces import TranscriptionService
from .utils import extract_audio_from_media


@dataclass
class GoogleCloudSpeechTranscriptionService(TranscriptionService):
    """Transcribe audio using Google Cloud Speech-to-Text."""

    language_code: str = "en-US"
    sample_rate_hz: int = 16000
    enable_automatic_punctuation: bool = True

    def __post_init__(self):
        if speech is None:
            raise ImportError("google-cloud-speech not installed. Install with `pip install google-cloud-speech`.")

    def transcribe(self, video_path: str, job_id: str) -> str:
        audio_path = extract_audio_from_media(
            video_path,
            job_id,
            format="wav",
            sample_rate=self.sample_rate_hz,
            channels=1,
        )
        logger.log_step(job_id, "TRANSCRIPTION_GCP", "Submitting audio to Google Cloud Speech")

        client = speech.SpeechClient()
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()

        recognition_audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.sample_rate_hz,
            language_code=self.language_code,
            enable_automatic_punctuation=self.enable_automatic_punctuation,
        )

        response = client.recognize(config=config, audio=recognition_audio)
        transcript = " ".join(result.alternatives[0].transcript for result in response.results)
        logger.log_step(job_id, "TRANSCRIPTION_COMPLETE", f"GCP Speech produced {len(transcript)} characters")
        return transcript.strip()
