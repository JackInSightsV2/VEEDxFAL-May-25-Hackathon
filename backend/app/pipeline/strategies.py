from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .context import PipelineContext
from .interfaces import PipelineServices, StyleStrategy
from ..logger import logger


STYLIZED_STYLES = {"Studio Ghibli", "Pixar", "Anime", "Watercolor", "Cyberpunk"}


def _resolve_audio_gender(gender: Optional[str], voice_style: Optional[str]) -> Optional[str]:
    if gender and gender.lower() in {"non-binary", "nonbinary", "non_binary"}:
        return voice_style or gender
    return gender or voice_style


class StylizedStrategy(StyleStrategy):
    name = "ASYNC_STYLIZED"

    async def run(self, ctx: PipelineContext) -> None:
        job_id = ctx.job_id
        services = self.services
        visual_style = ctx.visual_style or "Unknown"

        logger.log_step(
            job_id,
            "ASYNC_STYLIZED_START",
            f"Starting async stylized pipeline for {visual_style}",
        )

        ctx.video_paths = await services.stylized_visuals.generate(ctx.key_phrases, job_id)
        if not ctx.video_paths:
            raise RuntimeError("Stylized pipeline failed to produce any videos")

        if len(ctx.video_paths) > 1:
            logger.log_step(job_id, "VIDEO_STITCH_START", "Stitching stylized clips...")
            ctx.stitched_video_path = services.video_stitcher.stitch(
                ctx.video_paths,
                logger.get_job_file_path(job_id, "stitched_video.mp4"),
            )
        else:
            ctx.stitched_video_path = ctx.video_paths[0]

        logger.log_step(job_id, "DURATION_DETECTION", "Detecting video duration...")
        video_duration = services.video_duration.duration(ctx.stitched_video_path)
        if not video_duration:
            video_duration = max(5.0, len(ctx.video_paths) * 5.0)
            logger.log_step(
                job_id,
                "DURATION_FALLBACK",
                f"Using estimated duration: {video_duration:.2f}s",
            )
        ctx.metadata["video_duration"] = video_duration

        base_text = ctx.transcript or ctx.input_text or ""
        logger.log_step(
            job_id,
            "TEXT_GENERATION",
            f"Generating first-person text for stylized content ({visual_style})...",
        )
        generated_text = services.timed_text.generate(
            video_duration,
            base_text,
            job_id,
            key_phrases=ctx.key_phrases,
            third_person=False,
        )
        if not generated_text:
            generated_text = base_text
            logger.log_step(
                job_id,
                "TEXT_GENERATION_FALLBACK",
                "Using original transcript/text as fallback",
            )
        ctx.generated_text = generated_text

        logger.log_step(
            job_id,
            "AUDIO_START",
            f"Generating audio with timing-matched text for stylized content ({visual_style})...",
        )
        audio_gender = _resolve_audio_gender(ctx.gender, ctx.voice_style)
        ctx.audio_path = services.audio.synthesize(
            generated_text,
            job_id,
            gender=audio_gender,
        )

        ctx.final_video_path = logger.get_job_file_path(job_id, "final_narrated_video.mp4")
        logger.log_step(job_id, "FINAL_VIDEO_START", "Adding audio track to stylized video...")
        combined_video_path = services.audio_video_merge.merge(
            ctx.stitched_video_path,
            ctx.audio_path,
            ctx.final_video_path,
        )
        ctx.final_video_path = combined_video_path

        try:
            logger.log_step(job_id, "AZURE_UPLOAD_START", "Uploading stylized assets to storage...")
            ctx.azure_urls = services.final_uploader.upload(job_id, combined_video_path, ctx.audio_path)
            logger.log_step(
                job_id,
                "AZURE_UPLOAD_SUCCESS",
                f"Files uploaded to Azure: {list(ctx.azure_urls.keys())}",
            )
        except Exception as exc:
            logger.log_step(job_id, "AZURE_UPLOAD_ERROR", f"Failed to upload to Azure: {exc}")
            ctx.azure_urls = {}

        ctx.metadata.update(
            {
                "mode": self.name,
                "generated_videos": len(ctx.video_paths),
                "success_rate": f"{(len(ctx.video_paths) / max(len(ctx.key_phrases), 1)) * 100:.1f}%",
            }
        )


class DefaultVideoStrategy(StyleStrategy):
    name = "ASYNC"

    async def run(self, ctx: PipelineContext) -> None:
        job_id = ctx.job_id
        services = self.services

        logger.log_step(
            job_id,
            "VIDEO_GENERATION",
            f"Generating {len(ctx.key_phrases)} video clips...",
        )
        ctx.video_paths = await services.realistic_visuals.generate(ctx.key_phrases, job_id)
        if not ctx.video_paths:
            raise RuntimeError("Failed to generate any videos")

        if ctx.audio_path:
            logger.log_step(job_id, "STITCHING_START", f"Stitching {len(ctx.video_paths)} videos together...")
            ctx.final_video_path = services.video_assembler.create_final(
                ctx.video_paths,
                ctx.audio_path,
                job_id,
            )
            duration = services.video_duration.duration(ctx.final_video_path)
            if duration:
                ctx.metadata["video_duration"] = duration
        else:
            logger.log_step(job_id, "STITCHING_START", f"Stitching {len(ctx.video_paths)} videos together...")
            ctx.stitched_video_path = services.video_stitcher.stitch(
                ctx.video_paths,
                logger.get_job_file_path(job_id, "stitched_video.mp4"),
            )

            logger.log_step(job_id, "DURATION_DETECTION", "Detecting video duration...")
            video_duration = services.video_duration.duration(ctx.stitched_video_path)
            if not video_duration:
                video_duration = len(ctx.video_paths) * 5.0
                logger.log_step(
                    job_id,
                    "DURATION_FALLBACK",
                    f"Using estimated duration: {video_duration:.2f}s",
                )
            ctx.metadata["video_duration"] = video_duration

            base_text = ctx.generated_text or ctx.transcript or ctx.input_text or ""
            logger.log_step(job_id, "TEXT_GENERATION", "Generating narration for realistic pipeline...")
            generated_text = services.timed_text.generate(
                video_duration,
                base_text,
                job_id,
                key_phrases=ctx.key_phrases,
                third_person=False,
            )
            if not generated_text:
                generated_text = base_text
                logger.log_step(
                    job_id,
                    "TEXT_GENERATION_FALLBACK",
                    "Using original text as fallback",
                )
            ctx.generated_text = generated_text

            logger.log_step(job_id, "AUDIO_START", "Generating audio narration...")
            audio_gender = _resolve_audio_gender(ctx.gender, ctx.voice_style)
            ctx.audio_path = services.audio.synthesize(
                generated_text,
                job_id,
                gender=audio_gender,
            )

            ctx.final_video_path = logger.get_job_file_path(job_id, "final_narrated_video.mp4")
            logger.log_step(job_id, "FINAL_VIDEO_START", "Combining stitched video with narration...")
            ctx.final_video_path = services.audio_video_merge.merge(
                ctx.stitched_video_path,
                ctx.audio_path,
                ctx.final_video_path,
            )

        try:
            logger.log_step(job_id, "AZURE_UPLOAD_START", "Uploading final video and audio to storage...")
            ctx.azure_urls = services.final_uploader.upload(job_id, ctx.final_video_path, ctx.audio_path or "")
            logger.log_step(
                job_id,
                "AZURE_UPLOAD_SUCCESS",
                f"Files uploaded to Azure: {list(ctx.azure_urls.keys())}",
            )
        except Exception as exc:
            logger.log_step(job_id, "AZURE_UPLOAD_ERROR", f"Failed to upload to Azure: {exc}")
            ctx.azure_urls = {}

        ctx.metadata.update(
            {
                "mode": self.name,
                "generated_videos": len(ctx.video_paths),
                "success_rate": f"{(len(ctx.video_paths) / max(len(ctx.key_phrases), 1)) * 100:.1f}%",
            }
        )


@dataclass
class BlogAvatarConfig:
    name: str
    default_avatar: str
    upload_prefix: str


class BlogAvatarStrategy(StyleStrategy):
    name = "BLOG_AVATAR"

    def __init__(self, services: PipelineServices, config: BlogAvatarConfig):
        super().__init__(services)
        self.config = config

    @staticmethod
    def _pronoun_for_gender(gender: Optional[str]) -> str:
        if not gender:
            return "they"
        lowered = gender.lower()
        if lowered == "female":
            return "she"
        if lowered == "male":
            return "he"
        if lowered in {"non-binary", "nonbinary", "non_binary"}:
            return "they"
        return "they"

    async def run(self, ctx: PipelineContext) -> None:
        job_id = ctx.job_id
        services = self.services

        pronouns = self._pronoun_for_gender(ctx.gender)
        gender_description = {
            "she": "female",
            "he": "male",
            "they": "non-binary person" if ctx.gender and ctx.gender.lower() in {"non-binary", "nonbinary", "non_binary"} else "person",
        }[pronouns]

        logger.log_step(
            job_id,
            "TEXT_GENERATION",
            f"Generating third-person story for blog avatar ({self.config.name})...",
        )

        base_text = ctx.transcript or ctx.input_text or ""
        story = services.timed_text.generate(
            25.0,
            base_text,
            job_id,
            third_person=True,
            person_name=ctx.person_name or pronouns,
        )
        if not story:
            replacements_map: Dict[str, Dict[str, str]] = {
                "he": {"I ": "He ", "my ": "his ", "me ": "him "},
                "she": {"I ": "She ", "my ": "her ", "me ": "her "},
                "they": {"I ": "They ", "my ": "their ", "me ": "them "},
            }
            replacements = replacements_map[pronouns]
            transformed = base_text
            for old, new in replacements.items():
                transformed = transformed.replace(old, new)
            subject = ctx.person_name or pronouns.capitalize()
            story = f"{subject} experienced an interesting day. {transformed}"
            logger.log_step(
                job_id,
                "TEXT_GENERATION_FALLBACK",
                f"Using simple third-person conversion for {gender_description}",
            )
        ctx.generated_text = story

        avatar_id = self.config.default_avatar
        upload_prefix = f"{self.config.upload_prefix}-about-{ctx.gender or 'user'}"
        if ctx.visual_style in {"blog-nonbinary", "blog-non-binary"}:
            if ctx.voice_style and ctx.voice_style.lower() == "male":
                avatar_id = "any_male_primary"
                upload_prefix = f"blog-nonbinary-male-about-{ctx.gender or 'user'}"
            else:
                avatar_id = "any_female_primary"
                upload_prefix = f"blog-nonbinary-female-about-{ctx.gender or 'user'}"
        elif self.config.name == "blog-female":
            avatar_id = "any_female_primary"
        elif self.config.name == "blog-male":
            avatar_id = "any_male_primary"

        logger.log_step(
            job_id,
            "AVATAR_VIDEO_START",
            f"Generating blog avatar video with avatar {avatar_id}...",
        )
        ctx.final_video_path = services.avatar_video.generate(story, avatar_id, 25.0, job_id)
        if not ctx.final_video_path:
            raise RuntimeError("Failed to generate blog avatar video")
        ctx.video_paths = [ctx.final_video_path]

        logger.log_step(job_id, "AZURE_UPLOAD_START", "Uploading blog avatar video to storage...")
        try:
            video_url = services.video_uploader.upload(ctx.final_video_path, job_id, upload_prefix)
            ctx.azure_urls = {"blog_video_url": video_url}
            logger.log_step(job_id, "AZURE_UPLOAD_SUCCESS", f"Blog video uploaded to Azure: {video_url}")
        except Exception as exc:
            logger.log_step(job_id, "AZURE_UPLOAD_ERROR", f"Failed to upload blog video: {exc}")
            ctx.azure_urls = {}

        ctx.metadata.update(
            {
                "mode": self.name,
                "avatar_gender": "male" if avatar_id == "any_male_primary" else "female",
                "story_about": gender_description,
                "upload_prefix": upload_prefix,
                "avatar_id": avatar_id,
                "voice_style": ctx.voice_style,
            }
        )
