from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import firebase_admin  # type: ignore
    from firebase_admin import credentials, storage  # type: ignore
except ImportError:  # pragma: no cover
    firebase_admin = None

from ..pipeline.interfaces import ImageUploadService, VideoUploadService


@dataclass
class FirebaseStorageUploadService(ImageUploadService, VideoUploadService):
    """Upload helper targeting Firebase Storage (built on Google Cloud Storage)."""

    bucket_name: str = ""
    credential_path: Optional[str] = None
    app_name: str = "video-pipeline"

    def __post_init__(self) -> None:
        if firebase_admin is None:
            raise ImportError("firebase-admin not installed. Install with `pip install firebase-admin`.")
        if not firebase_admin._apps:
            cred = credentials.Certificate(self.credential_path) if self.credential_path else credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"storageBucket": self.bucket_name}, name=self.app_name)
        self._bucket = storage.bucket(app=firebase_admin.get_app(self.app_name))

    def _upload(self, path: str, destination: str) -> str:
        blob = self._bucket.blob(destination)
        blob.upload_from_filename(path)
        blob.make_public()
        return blob.public_url

    def upload(self, image_path: str, job_id: str) -> str:
        destination = f"{job_id}/images/{image_path.split('/')[-1]}"
        return self._upload(image_path, destination)

    def upload_video(self, video_path: str, job_id: str, prefix: Optional[str] = None) -> str:
        destination = f"{job_id}/videos/{prefix or ''}{video_path.split('/')[-1]}"
        return self._upload(video_path, destination)
