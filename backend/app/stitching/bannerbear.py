from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import List, Optional

import requests

from ..logger import logger
from ..pipeline.interfaces import VideoAssemblerService


@dataclass
class BannerbearVideoAssembler(VideoAssemblerService):
    """Bannerbear template-based video assembly."""

    api_key: Optional[str] = None
    template_id: Optional[str] = None
    poll_interval: float = 4.0
    timeout_seconds: float = 240.0

    @property
    def _base_url(self) -> str:
        return "https://api.bannerbear.com/v2"

    def _headers(self) -> dict:
        key = self.api_key or os.getenv("BANNERBEAR_API_KEY")
        if not key:
            raise ValueError("Bannerbear API key not provided.")
        return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def create_final(self, video_paths: List[str], audio_path: str, job_id: str) -> str:
        if not self.template_id:
            raise ValueError("Bannerbear template_id must be provided.")

        modifications = [{"video_url": path} for path in video_paths]
        payload = {"template": self.template_id, "modifications": modifications, "audio_url": audio_path}
        response = requests.post(f"{self._base_url}/videos", json=payload, headers=self._headers(), timeout=30)
        response.raise_for_status()
        job = response.json()
        video_id = job.get("uid")

        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            poll = requests.get(f"{self._base_url}/videos/{video_id}", headers=self._headers(), timeout=15)
            poll.raise_for_status()
            payload = poll.json()
            status = payload.get("status")
            if status == "completed":
                final_url = payload.get("video_url")
                if not final_url:
                    raise RuntimeError("Bannerbear completed but no video_url returned.")
                final_path = logger.get_job_file_path(job_id, "bannerbear_final.mp4")
                download = requests.get(final_url, timeout=60)
                download.raise_for_status()
                with open(final_path, "wb") as file_out:
                    file_out.write(download.content)
                logger.log_step(job_id, "VIDEO_STITCHING", f"Bannerbear final video saved to {final_path}")
                return final_path
            if status == "error":
                raise RuntimeError(f"Bannerbear video failed: {payload.get('error')}")
            time.sleep(self.poll_interval)
        raise TimeoutError("Bannerbear render timed out.")
