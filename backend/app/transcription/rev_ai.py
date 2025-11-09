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
class RevAITranscriptionService(TranscriptionService):
    """Transcribe audio using Rev AI."""

    api_key: Optional[str] = None
    language: Optional[str] = None
    poll_interval: float = 5.0
    timeout_seconds: float = 600.0
    base_url: str = "https://api.rev.ai/speechtotext/v1"

    def _headers(self) -> dict:
        key = self.api_key or os.getenv("REVAI_API_KEY")
        if not key:
            raise ValueError("Rev AI API key not provided. Set REVAI_API_KEY or pass api_key.")
        return {"Authorization": f"Bearer {key}"}

    def _submit_job(self, audio_path: str) -> str:
        url = f"{self.base_url}/jobs"
        params = {}
        if self.language:
            params["language"] = self.language
        with open(audio_path, "rb") as audio_file:
            files = {"media": audio_file}
            response = requests.post(url, headers=self._headers(), data=params, files=files, timeout=120)
        response.raise_for_status()
        return response.json()["id"]

    def _poll_job(self, job_id: str) -> dict:
        url = f"{self.base_url}/jobs/{job_id}"
        deadline = time.time() + self.timeout_seconds
        while True:
            if time.time() > deadline:
                raise TimeoutError(f"Rev AI job {job_id} timed out.")
            response = requests.get(url, headers=self._headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            if status in {"transcribed", "failed"}:
                return data
            time.sleep(self.poll_interval)

    def _download_transcript(self, job_id: str) -> str:
        url = f"{self.base_url}/jobs/{job_id}/transcript"
        response = requests.get(url, headers=self._headers(), params={"format": "text"}, timeout=30)
        response.raise_for_status()
        return response.text

    def transcribe(self, video_path: str, job_id: str) -> str:
        audio_path = extract_audio_from_media(video_path, job_id, format="mp3")
        logger.log_step(job_id, "TRANSCRIPTION_REVAI", "Submitting audio to Rev AI")
        job_id_remote = self._submit_job(audio_path)
        result = self._poll_job(job_id_remote)
        if result.get("status") == "failed":
            raise RuntimeError(f"Rev AI transcription failed: {result.get('failure_detail')}")
        text = self._download_transcript(job_id_remote)
        logger.log_step(job_id, "TRANSCRIPTION_COMPLETE", f"Rev AI produced {len(text)} characters")
        return text.strip()
