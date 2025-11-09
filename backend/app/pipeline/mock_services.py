from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

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
from ..logger import logger


def _ensure_file(path: str | Path, content: str) -> str:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def _ensure_binary_file(path: str | Path, label: str) -> str:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(f"MOCK {label}".encode("utf-8"))
    return str(file_path)


class MockTranscriptionService(TranscriptionService):
    def transcribe(self, video_path: str, job_id: str) -> str:
        logger.log_step(job_id, "MOCK_TRANSCRIPTION", f"Transcribing {video_path}")
        return f"[Mock transcript for {Path(video_path).name}]"


class MockAnalysisService(AnalysisService):
    def analyze(self, text: str) -> Dict[str, object]:
        return {
            "sentiment": "balanced",
            "topics": ["mock topic 1", "mock topic 2"],
            "length": len(text),
        }


class MockKeyPhraseService(KeyPhraseService):
    def extract(
        self,
        text: str,
        sentiment_data: Dict[str, object],
        *,
        num_phrases: int,
        gender: Optional[str],
        age_group: Optional[str],
        visual_style: Optional[str],
    ) -> List[str]:
        sentences = [line.strip() for line in text.split(".") if line.strip()]
        phrases = sentences[:num_phrases] or [text]
        result = []
        for index, phrase in enumerate(phrases, start=1):
            descriptor = ", ".join(filter(None, [gender, age_group, visual_style]))
            descriptor = f" ({descriptor})" if descriptor else ""
            result.append(f"Mock prompt #{index}{descriptor}: {phrase}")
        return result


class MockScriptService(ScriptService):
    def build(
        self,
        transcript: str,
        mood: str,
        sentiment_data: Dict[str, object],
        *,
        gender: Optional[str],
        age_group: Optional[str],
        visual_style: Optional[str],
    ) -> str:
        return f"[Mock script: mood={mood}, style={visual_style}] {transcript}"


class MockTimedTextService(TimedTextService):
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
        persona = person_name or "the narrator"
        perspective = "they" if third_person else "I"
        phrases = ", ".join(list(key_phrases or [])[:3])
        return (
            f"[Mock timed text (~{duration_seconds:.1f}s)] "
            f"{persona} says ({perspective}) about: {phrases or source_text[:50]}"
        )


class MockAudioService(AudioService):
    def synthesize(self, text: str, job_id: str, *, gender: Optional[str]) -> str:
        audio_path = logger.get_job_file_path(job_id, "mock_audio.mp3")
        return _ensure_binary_file(audio_path, f"AUDIO gender={gender or 'neutral'} :: {text[:40]}")


class MockStylizedVisualService(StylizedVisualService):
    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        video_paths: List[str] = []
        for idx, phrase in enumerate(key_phrases):
            await asyncio.sleep(0)
            video_path = logger.get_job_file_path(job_id, f"mock_stylized_clip_{idx}.mp4")
            _ensure_binary_file(video_path, f"STYLIZED CLIP #{idx+1}: {phrase[:40]}")
            video_paths.append(video_path)
        return video_paths


class MockVideoGenerationService(VideoGenerationService):
    async def generate(self, key_phrases: List[str], job_id: str) -> List[str]:
        video_paths: List[str] = []
        for idx, phrase in enumerate(key_phrases):
            await asyncio.sleep(0)
            video_path = logger.get_job_file_path(job_id, f"mock_realistic_clip_{idx}.mp4")
            _ensure_binary_file(video_path, f"REALISTIC CLIP #{idx+1}: {phrase[:40]}")
            video_paths.append(video_path)
        return video_paths


class MockAvatarVideoService(AvatarVideoService):
    def generate(self, text: str, avatar_id: str, duration_seconds: float, job_id: str) -> str:
        video_path = logger.get_job_file_path(job_id, "mock_avatar_video.mp4")
        _ensure_binary_file(video_path, f"AVATAR {avatar_id} :: {text[:50]}")
        return video_path


class MockVideoAssemblerService(VideoAssemblerService):
    def create_final(self, video_paths: List[str], audio_path: str, job_id: str) -> str:
        final_path = logger.get_job_file_path(job_id, "mock_final_video.mp4")
        content = "\n".join(["Mock final video built from:"] + video_paths + [f"Audio: {audio_path}"])
        return _ensure_file(final_path, content)


class MockAudioVideoMergeService(AudioVideoMergeService):
    def merge(self, video_path: str, audio_path: str, output_path: str) -> str:
        return _ensure_file(output_path, f"Mock merged video <- {video_path} + {audio_path}")


class MockVideoStitcherService(VideoStitcherService):
    def stitch(self, video_paths: List[str], output_path: str) -> str:
        return _ensure_file(output_path, "\n".join(["Mock stitched sequence:"] + video_paths))


class MockVideoDurationService(VideoDurationService):
    def duration(self, video_path: str) -> Optional[float]:
        return 5.0


class MockFinalAssetUploadService(FinalAssetUploadService):
    def upload(self, job_id: str, video_path: str, audio_path: str) -> Dict[str, str]:
        return {
            "video_url": f"https://mock.storage/{Path(video_path).name}",
            "audio_url": f"https://mock.storage/{Path(audio_path).name}",
        }


class MockVideoUploadService(VideoUploadService):
    def upload(self, video_path: str, job_id: str, prefix: Optional[str] = None) -> str:
        slug = prefix or "mock"
        return f"https://mock.storage/{slug}/{Path(video_path).name}"


class MockImageUploadService(ImageUploadService):
    def upload(self, image_path: str, job_id: str) -> str:
        return f"https://mock.storage/images/{Path(image_path).name}"


@dataclass
class MockPipelineServices(PipelineServices):
    analysis: AnalysisService = MockAnalysisService()
    key_phrases: KeyPhraseService = MockKeyPhraseService()
    script: ScriptService = MockScriptService()
    timed_text: TimedTextService = MockTimedTextService()
    audio: AudioService = MockAudioService()
    stylized_visuals: StylizedVisualService = MockStylizedVisualService()
    realistic_visuals: VideoGenerationService = MockVideoGenerationService()
    avatar_video: AvatarVideoService = MockAvatarVideoService()
    video_assembler: VideoAssemblerService = MockVideoAssemblerService()
    audio_video_merge: AudioVideoMergeService = MockAudioVideoMergeService()
    video_stitcher: VideoStitcherService = MockVideoStitcherService()
    video_duration: VideoDurationService = MockVideoDurationService()
    final_uploader: FinalAssetUploadService = MockFinalAssetUploadService()
    video_uploader: VideoUploadService = MockVideoUploadService()
    image_uploader: ImageUploadService = MockImageUploadService()
    transcription: Optional[TranscriptionService] = MockTranscriptionService()


def build_mock_services() -> MockPipelineServices:
    return MockPipelineServices()
