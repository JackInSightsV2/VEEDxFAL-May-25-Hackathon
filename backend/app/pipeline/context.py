from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PipelineContext:
    """Mutable state shared across pipeline steps."""

    job_id: str
    mood: str
    request_type: str  # e.g. "video" or "text"

    # User-supplied metadata
    gender: Optional[str] = None
    age_group: Optional[str] = None
    visual_style: Optional[str] = None
    voice_style: Optional[str] = None
    person_name: Optional[str] = None

    # Core payload
    input_video_path: Optional[str] = None
    input_text: Optional[str] = None
    transcript: Optional[str] = None
    sentiment_data: Optional[Dict[str, Any]] = None
    key_phrases: List[str] = field(default_factory=list)
    generated_text: Optional[str] = None
    script_text: Optional[str] = None

    # Media artifacts
    audio_path: Optional[str] = None
    video_paths: List[str] = field(default_factory=list)
    stitched_video_path: Optional[str] = None
    final_video_path: Optional[str] = None

    # Outputs
    azure_urls: Dict[str, str] = field(default_factory=dict)

    # Miscellaneous bookkeeping
    metadata: Dict[str, Any] = field(default_factory=dict)

    def clone_shallow(self) -> "PipelineContext":
        """Return a shallow copy primarily for branching strategies."""
        return PipelineContext(
            job_id=self.job_id,
            mood=self.mood,
            request_type=self.request_type,
            gender=self.gender,
            age_group=self.age_group,
            visual_style=self.visual_style,
            voice_style=self.voice_style,
            person_name=self.person_name,
            input_video_path=self.input_video_path,
            input_text=self.input_text,
            transcript=self.transcript,
            sentiment_data=self.sentiment_data,
            key_phrases=list(self.key_phrases),
            generated_text=self.generated_text,
            audio_path=self.audio_path,
            video_paths=list(self.video_paths),
            stitched_video_path=self.stitched_video_path,
            final_video_path=self.final_video_path,
            azure_urls=dict(self.azure_urls),
            metadata=dict(self.metadata),
        )
