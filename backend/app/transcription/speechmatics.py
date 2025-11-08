from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import requests

from ..logger import logger
from ..pipeline.interfaces import TranscriptionService
from .utils import extract_audio_from_media


@dataclass
class SpeechmaticsTranscriptionService(TranscriptionService):
    """Transcribe audio using Speechmatics' API."""

    api_key: Optional[str] = None
    language: str = "en"
    operating_point: str = "standard"
    punctuate: bool = True
    diarize: bool = False
    poll_interval: float = 5.0
    timeout_seconds: float = 600.0
    base_url: str = "https://asr.api.speechmatics.com/v2"

    def _headers(self) -> dict:
        key = self.api_key or os.getenv("SPEECHMATICS_API_KEY")
        if not key:
            raise ValueError("Speechmatics API key not provided. Set SPEECHMATICS_API_KEY or pass api_key.")
        return {"Authorization": f"Bearer {key}"}

    def _job_config(self) -> Dict[str, object]:
        return {
            "type": "transcription",
            "transcription_config": {
                "language": self.language,
                "operating_point": self.operating_point,
                "enable_entities": False,
                "speaker_diarization": self.diarize,
                "enable_partials": False,
                "enable_punctuation": self.punctuate,
            },
        }

    def _submit_job(self, audio_path: str) -> str:
        url = f"{self.base_url}/jobs"
        files = {"data_file": open(audio_path, "rb")}
        data = {"config": json.dumps(self._job_config())}
        response = requests.post(url, headers=self._headers(), data=data, files=files, timeout=120)
        files["data_file"].close()
        response.raise_for_status()
        return response.json()["id"]

    def _poll_job(self, job_id: str) -> dict:
        url = f"{self.base_url}/jobs/{job_id}"
        deadline = time.time() + self.timeout_seconds
        while True:
            if time.time() > deadline:
                raise TimeoutError(f"Speechmatics job {job_id} timed out.")
            response = requests.get(url, headers=self._headers(), timeout=30)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            if status in {"done", "failed"}:
                return data
            time.sleep(self.poll_interval)

    def _download_transcript(self, job_id: str) -> str:
        url = f"{self.base_url}/jobs/{job_id}/transcript?format=txt"
        response = requests.get(url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.text

    def transcribe(self, video_path: str, job_id: str) -> str:
        audio_path = extract_audio_from_media(video_path, job_id, format="mp3")
        logger.log_step(job_id, "TRANSCRIPTION_SPEECHMATICS", "Submitting audio to Speechmatics")
        job_id_remote = self._submit_job(audio_path)
        result = self._poll_job(job_id_remote)
        if result.get("status") == "failed":
            raise RuntimeError(f"Speechmatics transcription failed: {result.get('error')}")  # type: ignore[index]
        text = self._download_transcript(job_id_remote)
        logger.log_step(job_id, "TRANSCRIPTION_COMPLETE", f"Speechmatics produced {len(text)} characters")
        return text.strip()
