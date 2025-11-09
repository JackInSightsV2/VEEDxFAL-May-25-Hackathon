from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import boto3

from ..pipeline.interfaces import ImageUploadService, VideoUploadService, FinalAssetUploadService


@dataclass
class S3UploadService(ImageUploadService, VideoUploadService):
    """Amazon S3 uploader for images, videos, and final assets."""

    bucket_name: str = ""
    region_name: Optional[str] = None

    def __post_init__(self) -> None:
        self._client = boto3.client("s3", region_name=self.region_name)

    def _upload_file(self, path: str, key: str) -> str:
        self._client.upload_file(path, self.bucket_name, key, ExtraArgs={"ACL": "public-read"})
        location = self._client.get_bucket_location(Bucket=self.bucket_name)["LocationConstraint"] or "us-east-1"
        return f"https://{self.bucket_name}.s3.{location}.amazonaws.com/{key}"

    def upload(self, image_path: str, job_id: str) -> str:
        key = f"{job_id}/images/{image_path.split('/')[-1]}"
        return self._upload_file(image_path, key)

    def upload_video(self, video_path: str, job_id: str, prefix: Optional[str] = None) -> str:
        key = f"{job_id}/videos/{(prefix or '')}{video_path.split('/')[-1]}"
        return self._upload_file(video_path, key)

class S3FinalAssetUploadService(FinalAssetUploadService):
    bucket_name: str = ""
    region_name: Optional[str] = None

    def __post_init__(self) -> None:
        self._client = boto3.client("s3", region_name=self.region_name)

    def _upload_file(self, path: str, key: str) -> str:
        self._client.upload_file(path, self.bucket_name, key, ExtraArgs={"ACL": "public-read"})
        location = self._client.get_bucket_location(Bucket=self.bucket_name)["LocationConstraint"] or "us-east-1"
        return f"https://{self.bucket_name}.s3.{location}.amazonaws.com/{key}"

    def upload(self, job_id: str, video_path: str, audio_path: str) -> dict:
        video_url = self._upload_file(video_path, f"{job_id}/final/{video_path.split('/')[-1]}")
        audio_url = self._upload_file(audio_path, f"{job_id}/final/{audio_path.split('/')[-1]}")
        return {"video_url": video_url, "audio_url": audio_url}
