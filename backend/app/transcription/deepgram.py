from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import requests

from ..logger import logger
from ..pipeline.interfaces import TranscriptionService
from .utils import extract_audio_from_media


@dataclass
class DeepgramTranscriptionService(TranscriptionService):
    """Transcribe audio using Deepgram's Speech-to-Text API."""

    api_key: Optional[str] = None
    model: Optional[str] = None
    language: Optional[str] = None
    api_url: str = "https://api.deepgram.com/v1/listen"

    def _headers(self) -> dict:
        key = self.api_key or os.getenv("DEEPGRAM_API_KEY")
        if not key:
            raise ValueError("Deepgram API key not provided. Set DEEPGRAM_API_KEY or pass api_key.")
        return {
            "Authorization": f"Token {key}",
            "Content-Type": "audio/mp3",
        }

    def _params(self) -> dict:
        params = {}
        if self.model:
            params["model"] = self.model
        if self.language:
            params["language"] = self.language
        return params

    def transcribe(self, video_path: str, job_id: str) -> str:
        audio_path = extract_audio_from_media(video_path, job_id, format="mp3")
        logger.log_step(job_id, "TRANSCRIPTION_DEEPGRAM", "Submitting audio to Deepgram")
        with open(audio_path, "rb") as audio_file:
            response = requests.post(
                self.api_url,
                headers=self._headers(),
                params=self._params(),
                data=audio_file,
                timeout=60,
            )
        response.raise_for_status()
        data = response.json()
        transcript = data.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
        logger.log_step(job_id, "TRANSCRIPTION_COMPLETE", f"Deepgram produced {len(transcript)} characters")
        return transcript.strip()
