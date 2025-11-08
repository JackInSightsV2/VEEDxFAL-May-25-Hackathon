from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

import requests

from ..logger import logger
from ..pipeline.interfaces import AudioService


@dataclass
class StableAudioService(AudioService):
    """Stable Audio API integration for background music or voice beds."""

    api_key: Optional[str] = None
    base_url: str = "https://api.stableaudio.com/v1"
    poll_interval: float = 3.0
    timeout_seconds: float = 180.0
    duration_seconds: float = 30.0

    def _headers(self) -> dict:
        key = self.api_key or os.getenv("STABLE_AUDIO_API_KEY")
        if not key:
            raise ValueError("Stable Audio API key not provided. Set STABLE_AUDIO_API_KEY or pass api_key.")
        return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def _create_job(self, prompt: str) -> dict:
        payload = {"prompt": prompt, "duration": self.duration_seconds}
        response = requests.post(f"{self.base_url}/generate", json=payload, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.json()

    def synthesize(self, text: str, job_id: str, *, gender: Optional[str]) -> str:
        prompt = f"Generate cinematic background music matching the mood: {gender or 'neutral voice'}.\n{text}"
        data = self._create_job(prompt)
        generation_id = data.get("id")
        audio_url = data.get("audio_url")

        if not audio_url and generation_id:
            deadline = time.time() + self.timeout_seconds
            while time.time() < deadline:
                status_resp = requests.get(
                    f"{self.base_url}/generate/{generation_id}",
                    headers=self._headers(),
                    timeout=15,
                )
                status_resp.raise_for_status()
                payload = status_resp.json()
                if payload.get("status") == "complete":
                    audio_url = payload.get("audio_url")
                    break
                if payload.get("status") == "failed":
                    raise RuntimeError(f"Stable Audio generation failed: {payload.get('error')}")
                time.sleep(self.poll_interval)

        if not audio_url:
            raise RuntimeError("Stable Audio did not return an audio URL.")

        audio_path = logger.get_job_file_path(job_id, "stable_audio.mp3")
        response = requests.get(audio_url, timeout=60)
        response.raise_for_status()
        with open(audio_path, "wb") as audio_file:
            audio_file.write(response.content)

        logger.log_step(job_id, "AUDIO_GENERATION_SUCCESS", f"Stable Audio content saved to {audio_path}")
        return audio_path
