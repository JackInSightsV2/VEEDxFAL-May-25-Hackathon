"""Voice synthesis using Resemble AI."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests

from .logger import logger
from .pipeline.interfaces import AudioService

RESEMBLE_BASE_URL = "https://api.resemble.ai/v2"

# Environment variable keys for gender-based defaults
VOICE_ENV_KEYS: Dict[str, str] = {
    "female": "RESEMBLE_VOICE_FEMALE_UUID",
    "male": "RESEMBLE_VOICE_MALE_UUID",
    "non-binary": "RESEMBLE_VOICE_NEUTRAL_UUID",
    "neutral": "RESEMBLE_VOICE_NEUTRAL_UUID",
}


class ResembleAIError(RuntimeError):
    """Custom error raised for Resemble AI failures."""


def _resolve_voice_uuid(gender: Optional[str], explicit_voice_id: Optional[str]) -> str:
    if explicit_voice_id:
        return explicit_voice_id
    if gender:
        gender_key = gender.lower()
        env_key = VOICE_ENV_KEYS.get(gender_key)
        if env_key:
            voice_uuid = os.getenv(env_key)
            if voice_uuid:
                return voice_uuid
    # Fall back to explicitly configured default
    default_uuid = os.getenv("RESEMBLE_DEFAULT_VOICE_UUID")
    if default_uuid:
        return default_uuid
    raise ResembleAIError(
        "No Resemble voice UUID configured. Set RESSEMBLE_VOICE_* environment variables "
        "or pass an explicit voice_id."
    )


def generate_voice_with_resemble(
    text: str,
    job_id: Optional[str] = None,
    *,
    voice_id: Optional[str] = None,
    gender: Optional[str] = None,
    sample_rate: int = 44100,
    output_format: str = "mp3",
    poll_interval: float = 1.0,
    timeout_seconds: float = 60.0,
) -> str:
    """Generate speech using Resemble AI and return the path to the saved file."""

    api_key = os.getenv("RESEMBLE_API_KEY")
    project_uuid = os.getenv("RESEMBLE_PROJECT_UUID")
    if not api_key:
        raise ResembleAIError("Missing RESEMBLE_API_KEY environment variable.")
    if not project_uuid:
        raise ResembleAIError("Missing RESEMBLE_PROJECT_UUID environment variable.")

    resolved_voice_uuid = _resolve_voice_uuid(gender, voice_id)

    title = f"job-{job_id or 'local'}-{int(time.time())}"
    payload = {
        "voice_uuid": resolved_voice_uuid,
        "text": text,
        "is_public": False,
        "is_archived": False,
        "title": title,
        "sample_rate": sample_rate,
        "output_format": output_format,
    }

    headers = {
        "Accept": "application/json",
        "Authorization": f"Token token={api_key}",
    }

    create_url = f"{RESEMBLE_BASE_URL}/projects/{project_uuid}/clips"
    response = requests.post(create_url, json=payload, headers=headers, timeout=30)
    if response.status_code >= 400:
        raise ResembleAIError(f"Resemble API create clip failed: {response.text}")
    clip_data = response.json().get("item")
    if not clip_data:
        raise ResembleAIError(f"Unexpected response from Resemble API: {response.text}")

    clip_uuid = clip_data.get("uuid")
    status = clip_data.get("status", "").lower()
    download_url = clip_data.get("download_url")

    deadline = time.time() + timeout_seconds
    while status not in {"complete", "success"}:
        if time.time() > deadline:
            raise ResembleAIError("Timed out waiting for Resemble clip to finish rendering.")
        time.sleep(poll_interval)
        poll_resp = requests.get(
            f"{RESEMBLE_BASE_URL}/clips/{clip_uuid}",
            headers=headers,
            timeout=15,
        )
        if poll_resp.status_code >= 400:
            raise ResembleAIError(f"Resemble API poll failed: {poll_resp.text}")
        clip_data = poll_resp.json().get("item", {})
        status = clip_data.get("status", "").lower()
        download_url = clip_data.get("download_url")

    if not download_url:
        raise ResembleAIError("Resemble clip completed but no download URL was returned.")

    audio_response = requests.get(download_url, timeout=30)
    if audio_response.status_code >= 400:
        raise ResembleAIError(f"Failed to download Resemble audio: {audio_response.text}")

    if job_id:
        output_path = logger.get_job_file_path(job_id, f"voice_resemble.{output_format}")
    else:
        output_path = f"voice_resemble.{output_format}"

    with open(output_path, "wb") as audio_file:
        audio_file.write(audio_response.content)

    logger.log_step(job_id or "SYSTEM", "AUDIO_GENERATION_SUCCESS", f"Resemble audio saved to {output_path}")
    return output_path


@dataclass
class ResembleAudioService(AudioService):
    """AudioService implementation powered by Resemble AI."""

    sample_rate: int = 44100
    output_format: str = "mp3"
    poll_interval: float = 1.0
    timeout_seconds: float = 60.0

    def synthesize(self, text: str, job_id: str, *, gender: Optional[str]) -> str:
        return generate_voice_with_resemble(
            text,
            job_id,
            gender=gender,
            sample_rate=self.sample_rate,
            output_format=self.output_format,
            poll_interval=self.poll_interval,
            timeout_seconds=self.timeout_seconds,
        )


__all__ = ["generate_voice_with_resemble", "ResembleAudioService", "ResembleAIError"]
