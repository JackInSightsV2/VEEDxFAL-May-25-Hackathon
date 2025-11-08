from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

import requests

from ..logger import logger
from ..pipeline.interfaces import TranscriptionService
from .utils import extract_audio_from_media


@dataclass
class AssemblyAITranscriptionService(TranscriptionService):
    """Transcribe audio using AssemblyAI."""

    api_key: Optional[str] = None
    language_code: Optional[str] = None
    poll_interval: float = 5.0
    timeout_seconds: float = 600.0

    upload_url: str = "https://api.assemblyai.com/v2/upload"
    transcript_url: str = "https://api.assemblyai.com/v2/transcript"

    def _headers(self) -> dict:
        key = self.api_key or os.getenv("ASSEMBLYAI_API_KEY")
        if not key:
            raise ValueError("AssemblyAI API key not provided. Set ASSEMBLYAI_API_KEY or pass api_key.")
        return {"authorization": key}

    def _upload_audio(self, audio_path: str) -> str:
        headers = self._headers()
        headers["content-type"] = "application/octet-stream"
        with open(audio_path, "rb") as audio_file:
            response = requests.post(self.upload_url, headers=headers, data=audio_file, timeout=120)
        response.raise_for_status()
        return response.json()["upload_url"]

    def _create_transcript(self, audio_url: str) -> str:
        payload = {"audio_url": audio_url}
        if self.language_code:
            payload["language_code"] = self.language_code
        response = requests.post(self.transcript_url, json=payload, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()["id"]

    def _poll_transcript(self, transcript_id: str) -> dict:
        endpoint = f"{self.transcript_url}/{transcript_id}"
        deadline = time.time() + self.timeout_seconds
        while True:
            if time.time() > deadline:
                raise TimeoutError(f"AssemblyAI transcription {transcript_id} timed out.")
            response = requests.get(endpoint, headers=self._headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            if status in {"completed", "error"}:
                return data
            time.sleep(self.poll_interval)

    def transcribe(self, video_path: str, job_id: str) -> str:
        audio_path = extract_audio_from_media(video_path, job_id, format="mp3")
        logger.log_step(job_id, "TRANSCRIPTION_ASSEMBLYAI", "Uploading audio to AssemblyAI")
        audio_url = self._upload_audio(audio_path)

        logger.log_step(job_id, "TRANSCRIPTION_ASSEMBLYAI", "Creating transcript job")
        transcript_id = self._create_transcript(audio_url)

        result = self._poll_transcript(transcript_id)
        if result.get("status") == "error":
            raise RuntimeError(f"AssemblyAI transcription failed: {result.get('error')}")

        text = result.get("text", "")
        logger.log_step(job_id, "TRANSCRIPTION_COMPLETE", f"AssemblyAI produced {len(text)} characters")
        return text.strip()
