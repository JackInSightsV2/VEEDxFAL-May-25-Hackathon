from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from ..pipeline.interfaces import TimedTextService
from .sonix import _build_srt, _split_sentences


@dataclass
class CaptionHubTimedTextService(TimedTextService):
    """CaptionHub-inspired timed text generator with simple chunk controls."""

    segment_duration: float = 3.5
    max_chars_per_segment: int = 90

    def _chunk(self, sentences: Iterable[str]) -> Iterable[str]:
        chunk = ""
        for sentence in sentences:
            if len(chunk) + len(sentence) + 1 <= self.max_chars_per_segment:
                chunk = f"{chunk} {sentence}".strip()
            else:
                if chunk:
                    yield chunk
                chunk = sentence
        if chunk:
            yield chunk

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
        sentences = list(_split_sentences(source_text))
        segments = list(self._chunk(sentences))
        if not segments:
            segments = [source_text.strip()]
        ideal_duration = duration_seconds / max(len(segments), 1)
        return _build_srt(segments, segment_duration=max(ideal_duration, self.segment_duration))
