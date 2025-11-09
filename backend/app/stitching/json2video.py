from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import List, Optional

import requests

from ..logger import logger
from ..pipeline.interfaces import VideoAssemblerService


@dataclass
class JSON2VideoAssembler(VideoAssemblerService):
    """JSON2Video template-based assembler."""

    api_key: Optional[str] = None
    base_url: str = "https://api.json2video.com/v2"
    template_id: Optional[str] = None
    poll_interval: float = 4.0
    timeout_seconds: float = 240.0

    def _headers(self) -> dict:
        key = self.api_key or os.getenv("JSON2VIDEO_API_KEY")
        if not key:
            raise ValueError("JSON2Video API key not provided.")
        return {"x-api-key": key, "Content-Type": "application/json"}

    def _build_payload(self, video_paths: List[str], audio_path: str) -> dict:
        return {
            "template_id": self.template_id,
            "timeline": [
                {"type": "video", "src": path} for path in video_paths
            ],
            "audio": {"src": audio_path},
        }

    def create_final(self, video_paths: List[str], audio_path: str, job_id: str) -> str:
        payload = self._build_payload(video_paths, audio_path)
        response = requests.post(f"{self.base_url}/render", headers=self._headers(), data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        job_info = response.json()
        job_identifier = job_info.get("id")
        if not job_identifier:
            raise RuntimeError("JSON2Video did not return a job id.")

        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            poll_response = requests.get(
                f"{self.base_url}/render/{job_identifier}",
                headers=self._headers(),
                timeout=15,
            )
            poll_response.raise_for_status()
            status_payload = poll_response.json()
            status = status_payload.get("status")
            if status == "completed":
                final_url = status_payload.get("url")
                if not final_url:
                    raise RuntimeError("JSON2Video completed but no URL provided.")
                final_path = logger.get_job_file_path(job_id, "json2video_final.mp4")
                download = requests.get(final_url, timeout=60)
                download.raise_for_status()
                with open(final_path, "wb") as file_out:
                    file_out.write(download.content)
                logger.log_step(job_id, "VIDEO_STITCHING", f"JSON2Video render saved to {final_path}")
                return final_path
            if status == "failed":
                raise RuntimeError(f"JSON2Video render failed: {status_payload.get('error')}")
            time.sleep(self.poll_interval)

        raise TimeoutError("JSON2Video render timed out.")
