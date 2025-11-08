from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from ..pipeline.interfaces import TimedTextService


def _split_sentences(text: str) -> Iterable[str]:
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _srt_timestamp(seconds: float) -> str:
    millis = int(seconds * 1000)
    hours, remainder = divmod(millis, 3600 * 1000)
    minutes, remainder = divmod(remainder, 60 * 1000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def _build_srt(sentences: Iterable[str], segment_duration: float = 4.5) -> str:
    srt_lines = []
    current_time = 0.0
    for idx, sentence in enumerate(sentences, start=1):
        start = _srt_timestamp(current_time)
        end = _srt_timestamp(current_time + segment_duration)
        srt_lines.append(f"{idx}")
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(sentence)
        srt_lines.append("")
        current_time += segment_duration
    return "\n".join(srt_lines).strip()


@dataclass
class SonixTimedTextService(TimedTextService):
    """Heuristic Sonix-style timed text generator.

    This implementation emulates Sonix behaviour by splitting text into
    sentence-sized segments and assigning uniform durations. Replace with
    direct Sonix API integration if needed.
    """

    segment_duration: float = 4.5

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
        if not sentences:
            sentences = [source_text.strip()]
        return _build_srt(sentences, segment_duration=self.segment_duration)
