from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

from ..logger import logger
from ..pipeline.interfaces import VideoAssemblerService


@dataclass
class PlainlyVideoAssembler(VideoAssemblerService):
    """Stub assembler representing services like Plainly or Idomoo."""

    provider_name: str = "Plainly"

    def create_final(self, video_paths: List[str], audio_path: str, job_id: str) -> str:
        final_path = logger.get_job_file_path(job_id, f"{self.provider_name.lower()}_final.mp4")
        metadata = {
            "provider": self.provider_name,
            "videos": video_paths,
            "audio": audio_path,
            "note": "Placeholder output. Integrate provider SDK/API to obtain rendered video.",
        }
        with open(final_path, "wb") as file_out:
            file_out.write(json.dumps(metadata, indent=2).encode("utf-8"))
        logger.log_step(job_id, "VIDEO_STITCHING", f"{self.provider_name} placeholder final video saved to {final_path}")
        return final_path
