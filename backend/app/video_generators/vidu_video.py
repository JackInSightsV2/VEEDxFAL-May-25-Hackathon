from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

from ..logger import logger
from ..pipeline.interfaces import VideoGenerationService


@dataclass
class ViduVideoGenerationService(VideoGenerationService):
    """Placeholder module for Vidu text-to-video generation."""

    default_duration: float = 9.0

    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        video_paths: List[str] = []
        for idx, phrase in enumerate(key_phrases):
            video_path = logger.get_job_file_path(job_id, f"vidu_clip_{idx}.mp4")
            metadata = {
                "provider": "Vidu",
                "prompt": phrase,
                "duration": self.default_duration,
                "note": "Placeholder clip. Hook into Vidu official API for real outputs.",
            }
            with open(video_path, "wb") as video_file:
                video_file.write(json.dumps(metadata, indent=2).encode("utf-8"))
            logger.log_step(job_id, "VIDEO_GENERATION", f"Vidu placeholder clip created: {video_path}")
            video_paths.append(video_path)
        return video_paths
