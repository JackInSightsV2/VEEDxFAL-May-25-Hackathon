from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from ..analysis.azure_language import AzureLanguageAnalysisService
from ..pipeline.interfaces import TimedTextService
from .sonix import _build_srt


@dataclass
class AzureLanguageTimedTextService(TimedTextService):
    """Timed text generation using Azure Text Analytics key phrases."""

    endpoint: str = ""
    api_key: Optional[str] = None
    language: Optional[str] = None
    base_segment_duration: float = 4.0

    def __post_init__(self) -> None:
        self._analysis = AzureLanguageAnalysisService(
            endpoint=self.endpoint,
            api_key=self.api_key,
            language=self.language,
        )

    def _segments_from_key_phrases(self, text: str, key_phrases: Iterable[str]) -> Iterable[str]:
        if not key_phrases:
            return [text.strip()]
        lowered = text.lower()
        positions = []
        for phrase in key_phrases:
            idx = lowered.find(phrase.lower())
            if idx >= 0:
                positions.append(idx)
        if not positions:
            return [text.strip()]
        positions = sorted(set(positions))
        segments = []
        last = 0
        for pos in positions:
            if pos - last > 20:
                segments.append(text[last:pos].strip())
                last = pos
        segments.append(text[last:].strip())
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
        phrases = key_phrases or analysis.get("topics", [])
        segments = list(self._segments_from_key_phrases(source_text, phrases))
        if not segments:
            segments = [source_text.strip()]
        segment_duration = max(duration_seconds / max(len(segments), 1), self.base_segment_duration)
        return _build_srt(segments, segment_duration=segment_duration)
