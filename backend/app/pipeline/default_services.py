from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional
from .interfaces import (
    AnalysisService,
    AudioService,
    AudioVideoMergeService,
    AvatarVideoService,
    FinalAssetUploadService,
    ImageUploadService,
    KeyPhraseService,
    PipelineServices,
    ScriptService,
    StylizedVisualService,
    TimedTextService,
    TranscriptionService,
    VideoAssemblerService,
    VideoDurationService,
    VideoGenerationService,
    VideoStitcherService,
    VideoUploadService,
)

from ..azure_uploader import upload_final_outputs, upload_image, upload_video
from ..elevenlabs import generate_voice
from ..fal import (
    async_generate_video_from_image,
    async_generate_videos_from_phrases,
    generate_blog_avatar_video,
)
from ..logger import logger
from ..openai_image import async_generate_image_with_openai
from ..utils import beautify_transcript
from ..video_assembler import add_audio_to_video, create_final_video
# video_stitcher / video_utils / test_pipeline live at the backend project root
# (alongside the `app` package), not inside `app`, so they are imported as
# top-level modules — `uvicorn app.main:app` runs with that root on sys.path.
from video_stitcher import stitch_videos
from video_utils import get_video_duration
from ..transcription.google_cloud_stt import GoogleCloudSpeechTranscriptionService
from ..analysis.google_nlp import GoogleNLPAnalysisService
from ..analysis.keyphrase_torch import TorchKeyPhraseService


class GCPAnalysisService(AnalysisService):
    def __init__(self) -> None:
        self._impl = GoogleNLPAnalysisService()

    def analyze(self, text: str) -> Dict[str, Any]:
        return self._impl.analyze(text)


class DefaultKeyPhraseService(KeyPhraseService):
    def __init__(self) -> None:
        self._impl = TorchKeyPhraseService()

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
        return self._impl.extract(
            text,
            sentiment_data,
            num_phrases=num_phrases,
            gender=gender,
            age_group=age_group,
            visual_style=visual_style,
        )


class DefaultScriptService(ScriptService):
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
        return beautify_transcript(
            transcript,
            mood,
            sentiment_data,
            gender=gender,
            age_group=age_group,
            visual_style=visual_style,
        )


class TimedTextForVideoService(TimedTextService):
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
        from test_pipeline import generate_text_for_video_length

        return generate_text_for_video_length(
            duration_seconds,
            source_text,
            job_id,
            key_phrases=key_phrases,
            third_person=third_person,
            person_name=person_name,
        )


class ElevenLabsAudioService(AudioService):
    def synthesize(self, text: str, job_id: str, *, gender: Optional[str]) -> str:
        return generate_voice(text, job_id, gender=gender)


class AsyncStylizedVisualService(StylizedVisualService):
    def __init__(self, image_uploader: ImageUploadService):
        self.image_uploader = image_uploader

    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        image_tasks: List[asyncio.Task] = []
        image_paths: List[str] = []

        for idx, phrase in enumerate(key_phrases):
            image_path = logger.get_job_file_path(job_id, f"openai_image_{idx}.png")
            image_paths.append(image_path)
            image_tasks.append(async_generate_image_with_openai(phrase, image_path))

        logger.log_step(
            job_id,
            "ASYNC_IMAGE_GENERATION",
            f"Generating {len(image_tasks)} images concurrently",
        )
        image_results = await asyncio.gather(*image_tasks, return_exceptions=True)

        successful_images: List[tuple[int, str, str]] = []
        for idx, result in enumerate(image_results):
            if isinstance(result, Exception):
                logger.log_step(job_id, "IMAGE_ERROR", f"Image {idx + 1} failed: {result}")
            else:
                logger.log_step(
                    job_id,
                    "IMAGE_SUCCESS",
                    f"Image {idx + 1} generated: {result}",
                )
                successful_images.append((idx, result, key_phrases[idx]))

        if not successful_images:
            raise RuntimeError("Failed to generate any images")

        retained_images: List[tuple[int, str, str]] = []
        for idx, path, phrase in successful_images:
            try:
                upload_url = self.image_uploader.upload(path, job_id)
                logger.log_step(
                    job_id,
                    "IMAGE_UPLOAD",
                    f"Image {idx + 1} uploaded: {upload_url}",
                )
                retained_images.append((idx, path, phrase))
            except Exception as exc:
                logger.log_step(
                    job_id,
                    "UPLOAD_ERROR",
                    f"Upload failed for image {idx + 1}: {exc}",
                )

        if not retained_images:
            raise RuntimeError("Failed to upload any images")

        video_tasks = [
            async_generate_video_from_image(image_path, phrase, idx, job_id)
            for idx, image_path, phrase in retained_images
        ]

        logger.log_step(
            job_id,
            "ASYNC_VIDEO_GENERATION",
            f"Generating {len(video_tasks)} videos concurrently",
        )
        video_results = await asyncio.gather(*video_tasks, return_exceptions=True)

        video_paths: List[str] = []
        for idx, result in enumerate(video_results):
            if isinstance(result, Exception):
                logger.log_step(job_id, "VIDEO_ERROR", f"Video {idx + 1} failed: {result}")
            else:
                logger.log_step(
                    job_id,
                    "VIDEO_SUCCESS",
                    f"Video {idx + 1} generated: {result}",
                )
                video_paths.append(result)

        if not video_paths:
            raise RuntimeError("Failed to generate any videos from images")

        logger.log_step(
            job_id,
            "ASYNC_STYLIZED_COMPLETE",
            f"Generated {len(video_paths)}/{len(key_phrases)} videos using async processing",
        )
        return video_paths


class AsyncVideoGenerationService(VideoGenerationService):
    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        return await async_generate_videos_from_phrases(key_phrases, job_id)


class AzureImageUploadService(ImageUploadService):
    def upload(self, image_path: str, job_id: str) -> str:
        return upload_image(image_path, job_id=job_id)


class AzureVideoUploadService(VideoUploadService):
    def upload(self, video_path: str, job_id: str, prefix: Optional[str] = None) -> str:
        return upload_video(video_path, job_id, prefix or "video")


class AzureFinalAssetUploadService(FinalAssetUploadService):
    def upload(self, job_id: str, video_path: str, audio_path: str) -> Dict[str, str]:
        return upload_final_outputs(job_id, video_path, audio_path)


class VideoAssembler(VideoAssemblerService):
    def create_final(self, video_paths: List[str], audio_path: str, job_id: str) -> str:
        return create_final_video(video_paths, audio_path, job_id)


class AudioVideoMerger(AudioVideoMergeService):
    def merge(self, video_path: str, audio_path: str, output_path: str) -> str:
        return add_audio_to_video(video_path, audio_path, output_path)


class VideoStitcher(VideoStitcherService):
    def stitch(self, video_paths: List[str], output_path: str) -> str:
        return stitch_videos(video_paths, output_path)


class VideoDuration(VideoDurationService):
    def duration(self, video_path: str) -> Optional[float]:
        return get_video_duration(video_path)


class BlogAvatarService(AvatarVideoService):
    def generate(self, text: str, avatar_id: str, duration_seconds: float, job_id: str) -> str:
        return generate_blog_avatar_video(text, avatar_id, 0, job_id)


@dataclass
class DefaultPipelineServices(PipelineServices):
    analysis: AnalysisService = GCPAnalysisService()
    key_phrases: KeyPhraseService = DefaultKeyPhraseService()
    script: ScriptService = DefaultScriptService()
    timed_text: TimedTextService = TimedTextForVideoService()
    audio: AudioService = ElevenLabsAudioService()
    image_uploader: ImageUploadService = AzureImageUploadService()
    stylized_visuals: StylizedVisualService = AsyncStylizedVisualService(image_uploader)
    realistic_visuals: VideoGenerationService = AsyncVideoGenerationService()
    avatar_video: AvatarVideoService = BlogAvatarService()
    video_assembler: VideoAssemblerService = VideoAssembler()
    audio_video_merge: AudioVideoMergeService = AudioVideoMerger()
    video_stitcher: VideoStitcherService = VideoStitcher()
    video_duration: VideoDurationService = VideoDuration()
    final_uploader: FinalAssetUploadService = AzureFinalAssetUploadService()
    video_uploader: VideoUploadService = AzureVideoUploadService()
    transcription: Optional[TranscriptionService] = GoogleCloudSpeechTranscriptionService()


def build_default_services(
    audio_service: Optional[AudioService] = None,
    analysis_service: Optional[AnalysisService] = None,
    key_phrase_service: Optional[KeyPhraseService] = None,
    script_service: Optional[ScriptService] = None,
    timed_text_service: Optional[TimedTextService] = None,
    stylized_visuals: Optional[StylizedVisualService] = None,
    realistic_visuals: Optional[VideoGenerationService] = None,
    transcription_service: Optional[TranscriptionService] = None,
) -> DefaultPipelineServices:
    """Factory to build the default service container."""
    services = DefaultPipelineServices()
    # Ensure stylized visuals service references the same uploader instance
    services.stylized_visuals = AsyncStylizedVisualService(services.image_uploader)
    if audio_service is not None:
        services.audio = audio_service
    if analysis_service is not None:
        services.analysis = analysis_service
    if key_phrase_service is not None:
        services.key_phrases = key_phrase_service
    if script_service is not None:
        services.script = script_service
    if timed_text_service is not None:
        services.timed_text = timed_text_service
    if stylized_visuals is not None:
        services.stylized_visuals = stylized_visuals
    if realistic_visuals is not None:
        services.realistic_visuals = realistic_visuals
    if transcription_service is not None:
        services.transcription = transcription_service
    return services
