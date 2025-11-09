from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4

import boto3
import requests

from ..logger import logger
from ..pipeline.interfaces import TranscriptionService
from .utils import extract_audio_from_media


@dataclass
class AmazonTranscribeService(TranscriptionService):
    """Transcribe audio using Amazon Transcribe (batch)."""

    language_code: str = "en-US"
    media_format: str = "mp3"
    region_name: Optional[str] = None
    s3_bucket: Optional[str] = None
    delete_s3_object: bool = True
    poll_interval: float = 5.0
    timeout_seconds: float = 600.0

    def _clients(self):
        region = self.region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        if not region:
            raise ValueError("AWS region must be set via AWS_REGION or provided to AmazonTranscribeService.")
        s3 = boto3.client("s3", region_name=region)
        transcribe = boto3.client("transcribe", region_name=region)
        return s3, transcribe, region

    def _ensure_bucket(self, bucket: Optional[str]) -> str:
        bucket = bucket or self.s3_bucket or os.getenv("AWS_TRANSCRIBE_BUCKET")
        if not bucket:
            raise ValueError("Amazon Transcribe requires an S3 bucket. Set AWS_TRANSCRIBE_BUCKET or pass s3_bucket.")
        return bucket

    def transcribe(self, video_path: str, job_id: str) -> str:
        s3_client, transcribe_client, region = self._clients()
        bucket = self._ensure_bucket(self.s3_bucket)

        audio_path = extract_audio_from_media(video_path, job_id, format=self.media_format)
        object_key = f"transcribe/{job_id or uuid4().hex}/{Path(audio_path).name}"
        logger.log_step(job_id, "TRANSCRIPTION_AWS_UPLOAD", f"Uploading audio to s3://{bucket}/{object_key}")
        s3_client.upload_file(audio_path, bucket, object_key)

        job_name = f"{job_id or uuid4().hex}-transcription"
        media_uri = f"s3://{bucket}/{object_key}"

        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": media_uri},
            MediaFormat=self.media_format,
            LanguageCode=self.language_code,
        )

        deadline = time.time() + self.timeout_seconds
        logger.log_step(job_id, "TRANSCRIPTION_AWS_POLL", f"Waiting for Amazon Transcribe job {job_name}")
        while True:
            if time.time() > deadline:
                raise TimeoutError(f"Amazon Transcribe job {job_name} timed out.")
            status_response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job = status_response["TranscriptionJob"]
            status = job["TranscriptionJobStatus"]
            if status in {"COMPLETED", "FAILED"}:
                break
            time.sleep(self.poll_interval)

        if status == "FAILED":
            raise RuntimeError(f"Amazon Transcribe job failed: {job.get('FailureReason')}")

        transcript_uri = job["Transcript"]["TranscriptFileUri"]
        transcript_response = requests.get(transcript_uri, timeout=30)
        transcript_response.raise_for_status()
        transcript_json = transcript_response.json()

        text = " ".join(item["transcript"] for item in transcript_json["results"]["transcripts"])
        logger.log_step(job_id, "TRANSCRIPTION_COMPLETE", f"Amazon Transcribe produced {len(text)} characters")

        if self.delete_s3_object:
            try:
                s3_client.delete_object(Bucket=bucket, Key=object_key)
            except Exception:
                logger.log_step(job_id, "TRANSCRIPTION_AWS_CLEANUP_FAILED", f"Unable to delete s3://{bucket}/{object_key}")

        return text.strip()
