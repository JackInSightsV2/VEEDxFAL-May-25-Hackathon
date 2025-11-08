from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from azure.storage.blob import BlobServiceClient  # type: ignore
except ImportError:  # pragma: no cover
    BlobServiceClient = None

from ..pipeline.interfaces import ImageUploadService, VideoUploadService


@dataclass
class AzureBlobUploadService(ImageUploadService, VideoUploadService):
    """Azure Blob Storage uploader."""

    connection_string: Optional[str] = None
    container: str = "assets"

    def __post_init__(self) -> None:
        if BlobServiceClient is None:
            raise ImportError("azure-storage-blob not installed. Install with `pip install azure-storage-blob`.")
        self._client = BlobServiceClient.from_connection_string(self.connection_string)
        self._container_client = self._client.get_container_client(self.container)
        if not self._container_client.exists():
            self._container_client.create_container()

    def _upload_file(self, local_path: str, blob_path: str) -> str:
        blob_client = self._container_client.get_blob_client(blob_path)
        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        return blob_client.url

    def upload(self, image_path: str, job_id: str) -> str:
        blob_path = f"{job_id}/images/{image_path.split('/')[-1]}"
        return self._upload_file(image_path, blob_path)

    def upload_video(self, video_path: str, job_id: str, prefix: Optional[str] = None) -> str:
        blob_path = f"{job_id}/videos/{(prefix or '')}{video_path.split('/')[-1]}"
        return self._upload_file(video_path, blob_path)
