from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List

from ..logger import logger
from ..pipeline.interfaces import StylizedVisualService


@dataclass
class WanAIImageService(StylizedVisualService):
    """Placeholder for Wan AI image generation (Chinese market)."""

    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        image_paths: List[str] = []
        for idx, phrase in enumerate(key_phrases):
            image_path = logger.get_job_file_path(job_id, f"wan_ai_image_{idx}.png")
            metadata = {
                "provider": "Wan AI",
                "prompt": phrase,
                "note": "Placeholder asset. Integrate official Wan AI SDK or REST API.",
            }
            with open(image_path, "wb") as image_file:
                image_file.write(json.dumps(metadata, indent=2).encode("utf-8"))
            logger.log_step(job_id, "IMAGE_GENERATION", f"Wan AI placeholder image created: {image_path}")
            image_paths.append(image_path)
        return image_paths
