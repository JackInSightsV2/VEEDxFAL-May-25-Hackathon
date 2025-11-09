from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

import requests

from ..logger import logger
from ..pipeline.interfaces import AudioService


@dataclass
class MurfAIAudioService(AudioService):
    """Murf AI voice generation wrapper (batch REST workflow)."""

    api_key: Optional[str] = None
    voice_id: Optional[str] = None
    base_url: str = "https://api.murf.ai/v1"
    poll_interval: float = 2.0
    timeout_seconds: float = 120.0

    def _headers(self) -> dict:
        key = self.api_key or os.getenv("MURF_API_KEY")
        if not key:
            raise ValueError("Murf AI API key not provided. Set MURF_API_KEY or pass api_key.")
        return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _create_project(self, text: str) -> dict:
        payload = {
            "voice": {"voiceId": self.voice_id or "en-US-Thomas"},
            "scriptType": "TEXT",
            "inputScript": text,
        }
        response = requests.post(f"{self.base_url}/speech/generate", json=payload, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def synthesize(self, text: str, job_id: str, *, gender: Optional[str]) -> str:
        logger.log_step(job_id, "AUDIO_GENERATION", "Requesting audio from Murf AI")
        data = self._create_project(text)
        audio_url = data.get("audioUrl")
        job_id_remote = data.get("jobId")

        if not audio_url and job_id_remote:
            # Poll job status
            deadline = time.time() + self.timeout_seconds
            while time.time() < deadline:
                status_resp = requests.get(
                    f"{self.base_url}/speech/{job_id_remote}",
                    headers=self._headers(),
                    timeout=15,
                )
                status_resp.raise_for_status()
                payload = status_resp.json()
                if payload.get("status") == "completed":
                    audio_url = payload.get("audioUrl")
                    break
                time.sleep(self.poll_interval)

        if not audio_url:
            raise RuntimeError("Failed to retrieve Murf AI audio URL.")

        audio_path = logger.get_job_file_path(job_id, "murf_ai.mp3")
        audio_response = requests.get(audio_url, timeout=60)
        audio_response.raise_for_status()
        with open(audio_path, "wb") as audio_file:
            audio_file.write(audio_response.content)

        logger.log_step(job_id, "AUDIO_GENERATION_SUCCESS", f"Murf AI audio saved to {audio_path}")
        return audio_path
