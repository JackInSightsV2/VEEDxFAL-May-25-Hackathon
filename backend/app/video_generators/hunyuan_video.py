from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

from ..logger import logger
from ..pipeline.interfaces import VideoGenerationService


@dataclass
class HunyuanVideoGenerationService(VideoGenerationService):
    """Placeholder for Tencent HunyuanVideo generation."""

    default_duration: float = 12.0

    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        video_paths: List[str] = []
        for idx, phrase in enumerate(key_phrases):
            video_path = logger.get_job_file_path(job_id, f"hunyuan_clip_{idx}.mp4")
            metadata = {
                "provider": "Tencent HunyuanVideo",
                "prompt": phrase,
                "duration": self.default_duration,
                "note": "Placeholder clip. Implement real HunyuanVideo client as needed.",
            }
            with open(video_path, "wb") as video_file:
                video_file.write(json.dumps(metadata, indent=2).encode("utf-8"))
            logger.log_step(job_id, "VIDEO_GENERATION", f"Hunyuan placeholder clip created: {video_path}")
            video_paths.append(video_path)
        return video_paths
