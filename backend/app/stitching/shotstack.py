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
class ShotstackVideoAssembler(VideoAssemblerService):
    """Shotstack API orchestration for templated video assembly."""

    api_key: Optional[str] = None
    region: str = "ap-southeast-2"
    poll_interval: float = 5.0
    timeout_seconds: float = 300.0

    @property
    def _base_url(self) -> str:
        return f"https://api.{self.region}.shotstack.io/stage"

    def _headers(self) -> dict:
        key = self.api_key or os.getenv("SHOTSTACK_API_KEY")
        if not key:
            raise ValueError("Shotstack API key not provided.")
        return {"x-api-key": key, "Content-Type": "application/json"}

    def _submit_render(self, video_paths: List[str], audio_path: str, job_id: str) -> str:
        timeline = {
            "soundtrack": {"src": audio_path},
            "tracks": [
                {
                    "clips": [
                        {"asset": {"type": "video", "src": path}, "start": idx * 5, "length": 5}
                        for idx, path in enumerate(video_paths)
                    ]
                }
            ],
        }
        payload = {"timeline": timeline, "output": {"format": "mp4"}}
        response = requests.post(f"{self._base_url}/render", headers=self._headers(), data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        return response.json()["response"]["id"]

    def create_final(self, video_paths: List[str], audio_path: str, job_id: str) -> str:
        render_id = self._submit_render(video_paths, audio_path, job_id)

        deadline = time.time() + self.timeout_seconds
        status_url = f"{self._base_url}/render/{render_id}"
        while time.time() < deadline:
            response = requests.get(status_url, headers=self._headers(), timeout=15)
            response.raise_for_status()
            payload = response.json()["response"]
            status = payload["status"]
            if status == "done":
                final_url = payload["output"]["url"]
                final_path = logger.get_job_file_path(job_id, "shotstack_final.mp4")
                video_response = requests.get(final_url, timeout=60)
                video_response.raise_for_status()
                with open(final_path, "wb") as file_out:
                    file_out.write(video_response.content)
                logger.log_step(job_id, "VIDEO_STITCHING", f"Shotstack render completed: {final_path}")
                return final_path
            if status == "failed":
                raise RuntimeError(f"Shotstack rendering failed: {payload.get('error')}")
            time.sleep(self.poll_interval)

        raise TimeoutError("Shotstack render timed out.")
