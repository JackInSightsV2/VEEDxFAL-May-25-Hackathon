from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from keybert import KeyBERT  # type: ignore
except ImportError:  # pragma: no cover
    KeyBERT = None

from ..pipeline.interfaces import ScriptService


@dataclass
class KeyBERTScriptService(ScriptService):
    """Heuristic script generator using KeyBERT to extract core ideas."""

    model_name: str = "all-MiniLM-L6-v2"
    num_keywords: int = 8

    def __post_init__(self) -> None:
        if KeyBERT is None:
            raise ImportError("keybert not installed. Install with `pip install keybert`.")
        self._model = KeyBERT(model=self.model_name)

    def build(
        self,
        transcript: str,
        mood: str,
        sentiment_data: dict,
        *,
        gender: Optional[str],
        age_group: Optional[str],
        visual_style: Optional[str],
    ) -> str:
        keywords = self._model.extract_keywords(
            transcript,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=self.num_keywords,
        )
        bullet_points = [kw for kw, _ in keywords]

        script = [
            f"Tone: {mood}",
            f"Audience: {gender or 'unspecified'} / {age_group or 'all ages'}",
            f"Visual cues: {visual_style or 'neutral'}",
            "",
            "Key Ideas:",
        ]
        script.extend(f"- {point}" for point in bullet_points)

        script.append("")
        script.append("Suggested Outline:")
        for idx, point in enumerate(bullet_points, start=1):
            script.append(f"{idx}. {point}. Expand with personal anecdote or sensory detail.")

        return "\n".join(script)
