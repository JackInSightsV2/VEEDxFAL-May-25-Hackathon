from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from supabase import create_client, Client  # type: ignore
except ImportError:  # pragma: no cover
    create_client = None

from ..pipeline.interfaces import ImageUploadService, VideoUploadService


@dataclass
class SupabaseStorageService(ImageUploadService, VideoUploadService):
    """Supabase storage uploader."""

    url: str = ""
    api_key: str = ""
    bucket: str = "assets"

    def __post_init__(self) -> None:
        if create_client is None:
            raise ImportError("supabase-py not installed. Install with `pip install supabase`.")
        self._client: Client = create_client(self.url, self.api_key)

    def _upload(self, path: str, dest_path: str) -> str:
        storage_client = self._client.storage()
        storage_client.from_(self.bucket).upload(dest_path, path, {"cacheControl": "3600", "upsert": True})
        public_url = storage_client.from_(self.bucket).get_public_url(dest_path)
        return public_url

    def upload(self, image_path: str, job_id: str) -> str:
        dest = f"{job_id}/images/{image_path.split('/')[-1]}"
        return self._upload(image_path, dest)

    def upload_video(self, video_path: str, job_id: str, prefix: Optional[str] = None) -> str:
        dest = f"{job_id}/videos/{(prefix or '')}{video_path.split('/')[-1]}"
        return self._upload(video_path, dest)
