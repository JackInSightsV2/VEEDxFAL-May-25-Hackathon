from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .context import PipelineContext
from .default_services import build_default_services
from .interfaces import PipelineServices, StyleStrategy
from .strategies import (
    BlogAvatarConfig,
    BlogAvatarStrategy,
    DefaultVideoStrategy,
    STYLIZED_STYLES,
    StylizedStrategy,
    _resolve_audio_gender,
)
from ..logger import logger


BLOG_CONFIGS = {
    "blog-female": BlogAvatarConfig("blog-female", "any_female_primary", "blog-female"),
    "blog-male": BlogAvatarConfig("blog-male", "any_male_primary", "blog-male"),
    "blog-nonbinary": BlogAvatarConfig("blog-nonbinary", "any_female_primary", "blog-nonbinary"),
    "blog-non-binary": BlogAvatarConfig("blog-nonbinary", "any_female_primary", "blog-nonbinary"),
}


@dataclass
class PipelineResult:
    context: PipelineContext
    strategy: StyleStrategy


class PipelineOrchestrator:
    """Coordinates the modular pipeline flow using the configured services."""

    def __init__(self, services: Optional[PipelineServices] = None):
        self.services = services or build_default_services()

    def _select_strategy(self, ctx: PipelineContext) -> StyleStrategy:
        visual_style = ctx.visual_style or ""
        style_alias = str(ctx.metadata.get("style_alias") or "").lower()
        if style_alias in BLOG_CONFIGS:
            return BlogAvatarStrategy(self.services, BLOG_CONFIGS[style_alias])
        if visual_style in STYLIZED_STYLES:
            return StylizedStrategy(self.services)
        return DefaultVideoStrategy(self.services)

    def _ensure_text_payload(self, ctx: PipelineContext) -> str:
        if ctx.request_type == "video":
            if not ctx.input_video_path:
                raise ValueError("Video pipeline requires an input video path")
            if not ctx.transcript:
                if not self.services.transcription:
                    raise ValueError("No transcription service configured")
                logger.log_step(ctx.job_id, "TRANSCRIPTION_START", "Starting video transcription...")
                ctx.transcript = self.services.transcription.transcribe(ctx.input_video_path, ctx.job_id)
                logger.log_transcription(ctx.job_id, ctx.transcript)
            return ctx.transcript
        else:
            if not ctx.input_text:
                raise ValueError("Text pipeline requires an input text payload")
            return ctx.input_text

    def _run_shared_preprocessing(self, ctx: PipelineContext, base_text: str) -> None:
        logger.log_step(ctx.job_id, "ANALYSIS_START", "Analyzing transcript/text with NLP service...")
        ctx.sentiment_data = self.services.analysis.analyze(base_text)
        logger.log_analysis(ctx.job_id, ctx.sentiment_data)

        logger.log_step(ctx.job_id, "KEY_PHRASES_START", "Extracting key phrases for visual generation...")
        ctx.key_phrases = self.services.key_phrases.extract(
            base_text,
            ctx.sentiment_data,
            num_phrases=5,
            gender=ctx.gender,
            age_group=ctx.age_group,
            visual_style=ctx.visual_style,
        )
        logger.log_key_phrases(ctx.job_id, ctx.key_phrases)

        if ctx.request_type == "video":
            logger.log_step(ctx.job_id, "SCRIPT_CREATION", "Creating narration script...")
            ctx.script_text = self.services.script.build(
                base_text,
                ctx.mood,
                ctx.sentiment_data,
                gender=ctx.gender,
                age_group=ctx.age_group,
                visual_style=ctx.visual_style,
            )
            ctx.generated_text = ctx.script_text

            logger.log_step(ctx.job_id, "AUDIO_START", "Generating audio narration...")
            audio_gender = _resolve_audio_gender(ctx.gender, ctx.voice_style)
            ctx.audio_path = self.services.audio.synthesize(
                ctx.script_text,
                ctx.job_id,
                gender=audio_gender,
            )
            logger.log_audio_generation(ctx.job_id, ctx.script_text, ctx.audio_path)

    async def run(self, ctx: PipelineContext) -> PipelineResult:
        base_text = self._ensure_text_payload(ctx)

        strategy = self._select_strategy(ctx)
        logger.log_step(ctx.job_id, "PIPELINE_STRATEGY", f"Using strategy: {strategy.name}")

        self._run_shared_preprocessing(ctx, base_text)

        await strategy.run(ctx)

        return PipelineResult(context=ctx, strategy=strategy)
