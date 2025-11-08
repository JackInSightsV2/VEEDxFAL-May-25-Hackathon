from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from ..logger import logger


def extract_audio_from_media(
    media_path: str,
    job_id: Optional[str],
    *,
    sample_rate: int = 16000,
    channels: int = 1,
    format: str = "wav",
    overwrite: bool = True,
) -> str:
    """Extract audio from a media file using ffmpeg."""

    suffix = f".{format}"
    if job_id:
        audio_path = logger.get_job_file_path(job_id, f"transcribe_input{suffix}")
    else:
        audio_path = Path(media_path).with_suffix(suffix)

    cmd = [
        "ffmpeg",
        "-y" if overwrite else "-n",
        "-i",
        media_path,
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        audio_path,
    ]

    # Flatten command to strings
    cmd = [str(part) for part in cmd]
    completed = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Failed to extract audio with ffmpeg. stderr: {completed.stderr.decode('utf-8', errors='ignore')}"
        )
    return str(audio_path)
