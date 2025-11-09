from __future__ import annotations

import abc
from typing import Any, Dict, Iterable, List, Optional, Protocol


class TranscriptionService(Protocol):
    def transcribe(self, video_path: str, job_id: str) -> str:
        ...


class AnalysisService(Protocol):
    def analyze(self, text: str) -> Dict[str, Any]:
        ...


class KeyPhraseService(Protocol):
    def extract(
        self,
        text: str,
        sentiment_data: Dict[str, Any],
        *,
        num_phrases: int,
        gender: Optional[str],
        age_group: Optional[str],
        visual_style: Optional[str],
    ) -> List[str]:
        ...


class ScriptService(Protocol):
    def build(
        self,
        transcript: str,
        mood: str,
        sentiment_data: Dict[str, Any],
        *,
        gender: Optional[str],
        age_group: Optional[str],
        visual_style: Optional[str],
    ) -> str:
        ...


class TimedTextService(Protocol):
    def generate(
        self,
        duration_seconds: float,
        source_text: str,
        job_id: str,
        *,
        key_phrases: Optional[Iterable[str]] = None,
        third_person: bool = False,
        person_name: Optional[str] = None,
    ) -> str:
        ...


class AudioService(Protocol):
    def synthesize(self, text: str, job_id: str, *, gender: Optional[str]) -> str:
        ...


class StylizedVisualService(Protocol):
    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        ...


class VideoGenerationService(Protocol):
    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        ...


class ImageUploadService(Protocol):
    def upload(self, image_path: str, job_id: str) -> str:
        ...


class VideoUploadService(Protocol):
    def upload(self, video_path: str, job_id: str, prefix: Optional[str] = None) -> str:
        ...


class FinalAssetUploadService(Protocol):
    def upload(self, job_id: str, video_path: str, audio_path: str) -> Dict[str, str]:
        ...


class VideoAssemblerService(Protocol):
    def create_final(self, video_paths: List[str], audio_path: str, job_id: str) -> str:
        ...


class AudioVideoMergeService(Protocol):
    def merge(self, video_path: str, audio_path: str, output_path: str) -> str:
        ...


class VideoStitcherService(Protocol):
    def stitch(self, video_paths: List[str], output_path: str) -> str:
        ...


class VideoDurationService(Protocol):
    def duration(self, video_path: str) -> Optional[float]:
        ...


class AvatarVideoService(Protocol):
    def generate(self, text: str, avatar_id: str, duration_seconds: float, job_id: str) -> str:
        ...


class StyleStrategy(abc.ABC):
    name: str

    def __init__(self, services: "PipelineServices"):
        self.services = services

    @abc.abstractmethod
    async def run(self, ctx: "PipelineContext") -> None:
        ...


class PipelineServices(Protocol):
    transcription: Optional[TranscriptionService]
    analysis: AnalysisService
    key_phrases: KeyPhraseService
    script: ScriptService
    timed_text: TimedTextService
    audio: AudioService
    stylized_visuals: StylizedVisualService
    realistic_visuals: VideoGenerationService
    avatar_video: AvatarVideoService
    video_assembler: VideoAssemblerService
    audio_video_merge: AudioVideoMergeService
    video_stitcher: VideoStitcherService
    video_duration: VideoDurationService
    final_uploader: FinalAssetUploadService
    video_uploader: VideoUploadService
    image_uploader: ImageUploadService


# NOTE: This import is intentionally placed at the end to avoid circular imports.
from .context import PipelineContext
