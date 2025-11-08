from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import cloudinary  # type: ignore
    import cloudinary.uploader  # type: ignore
except ImportError:  # pragma: no cover
    cloudinary = None

from ..pipeline.interfaces import ImageUploadService, VideoUploadService


@dataclass
class CloudinaryUploadService(ImageUploadService, VideoUploadService):
    """Cloudinary-based uploader for images and videos."""

    cloud_name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    folder: Optional[str] = None

    def __post_init__(self) -> None:
        if cloudinary is None:
            raise ImportError("cloudinary not installed. Install with `pip install cloudinary`.")
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    def upload(self, image_path: str, job_id: str) -> str:
        result = cloudinary.uploader.upload(image_path, folder=self.folder or f"jobs/{job_id}")
        return result["secure_url"]

    def upload_video(self, video_path: str, job_id: str, prefix: Optional[str] = None) -> str:
        result = cloudinary.uploader.upload(
            video_path,
            folder=self.folder or f"jobs/{job_id}",
            resource_type="video",
            public_id=prefix,
        )
        return result["secure_url"]
