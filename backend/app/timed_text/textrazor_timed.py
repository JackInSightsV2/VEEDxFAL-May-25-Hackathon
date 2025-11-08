from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from ..analysis.textrazor_service import TextRazorAnalysisService
from ..pipeline.interfaces import TimedTextService
from .sonix import _build_srt


@dataclass
class TextRazorTimedTextService(TimedTextService):
    """Timed text generator leveraging TextRazor topics/entities."""

    api_key: Optional[str] = None
    base_segment_duration: float = 4.0

    def __post_init__(self) -> None:
        self._analysis = TextRazorAnalysisService(api_key=self.api_key)

    def _segments_from_topics(self, text: str, topics: Iterable[str]) -> Iterable[str]:
        if not topics:
            return [text.strip()]
        lowered = text.lower()
        segments = []
        last_index = 0
        for topic in topics:
            idx = lowered.find(topic.lower())
            if idx > last_index:
                segments.append(text[last_index:idx].strip())
                last_index = idx
        segments.append(text[last_index:].strip())
        return [segment for segment in segments if segment]

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
        analysis = self._analysis.analyze(source_text)
        topics = key_phrases or analysis.get("topics", [])
        segments = list(self._segments_from_topics(source_text, topics))
        if not segments:
            segments = [source_text.strip()]
        segment_duration = max(duration_seconds / max(len(segments), 1), self.base_segment_duration)
        return _build_srt(segments, segment_duration=segment_duration)
