from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import cohere  # type: ignore
except ImportError:  # pragma: no cover
    cohere = None

from ..pipeline.interfaces import ScriptService


@dataclass
class CohereScriptService(ScriptService):
    """Script generation using Cohere's text generation endpoint."""

    api_key: Optional[str] = None
    model: str = "command-r-plus"
    temperature: float = 0.6
    max_tokens: int = 700

    def __post_init__(self) -> None:
        if cohere is None:
            raise ImportError("cohere not installed. Install with `pip install cohere`.")
        if not self.api_key:
            raise ValueError("Cohere API key must be provided.")
        self._client = cohere.Client(self.api_key)

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
        prompt = (
            "Rewrite the supplied transcript into a polished narration for a short-form video. "
            f"Target mood: {mood}. Sentiment summary: {sentiment_data.get('sentiment')}.\n"
            f"Audience gender: {gender or 'unspecified'}, age group: {age_group or 'unspecified'}, "
            f"visual aesthetic: {visual_style or 'neutral'}.\n\nTranscript:\n{transcript}"
        )
        response = self._client.generate(
            model=self.model,
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response.generations[0].text.strip()
