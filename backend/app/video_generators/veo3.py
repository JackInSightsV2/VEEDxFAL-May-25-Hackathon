from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

from ..logger import logger
from ..pipeline.interfaces import VideoGenerationService


@dataclass
class Veo3VideoGenerationService(VideoGenerationService):
    """Placeholder for Google Veo 3 text-to-video generation."""

    default_duration: float = 10.0

    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        video_paths: List[str] = []
        for idx, phrase in enumerate(key_phrases):
            video_path = logger.get_job_file_path(job_id, f"veo3_clip_{idx}.mp4")
            metadata = {
                "provider": "Google Veo 3",
                "prompt": phrase,
                "duration": self.default_duration,
                "note": "Placeholder clip. Replace with actual Veo 3 API call.",
            }
            with open(video_path, "wb") as video_file:
                video_file.write(json.dumps(metadata, indent=2).encode("utf-8"))
            logger.log_step(job_id, "VIDEO_GENERATION", f"Veo 3 placeholder clip created: {video_path}")
            video_paths.append(video_path)
        return video_paths
