from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from ..pipeline.interfaces import TimedTextService
from .sonix import _build_srt, _split_sentences


@dataclass
class VeedTimedTextService(TimedTextService):
    """Veed-style timed text generator using key phrases to anchor segments."""

    base_segment_duration: float = 4.0

    def _segment_by_key_phrases(self, text: str, key_phrases: Iterable[str]) -> Iterable[str]:
        sentences = list(_split_sentences(text))
        if not key_phrases:
            return sentences

        segments = []
        buffer = []
        for sentence in sentences:
            buffer.append(sentence)
            if any(phrase.lower() in sentence.lower() for phrase in key_phrases):
                segments.append(" ".join(buffer))
                buffer = []
        if buffer:
            segments.append(" ".join(buffer))
        return segments

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
        segments = list(self._segment_by_key_phrases(source_text, key_phrases or []))
        if not segments:
            segments = [source_text.strip()]
        segment_duration = max(duration_seconds / max(len(segments), 1), self.base_segment_duration)
        return _build_srt(segments, segment_duration=segment_duration)
