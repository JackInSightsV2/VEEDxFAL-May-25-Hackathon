from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import anthropic  # type: ignore
except ImportError:  # pragma: no cover
    anthropic = None

from ..pipeline.interfaces import ScriptService


@dataclass
class AnthropicScriptService(ScriptService):
    """Narrative generation using Anthropic Claude."""

    api_key: Optional[str] = None
    model: str = "claude-3-opus-20240229"
    max_tokens: int = 1200
    temperature: float = 0.6

    def __post_init__(self) -> None:
        if anthropic is None:
            raise ImportError("anthropic package not installed. Install with `pip install anthropic`.")
        if not self.api_key:
            raise ValueError("Anthropic API key must be provided.")
        self._client = anthropic.Anthropic(api_key=self.api_key)

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
            "Craft a compelling narrative script intended for a narrated short-form video. "
            f"Target tone: {mood}. Sentiment context: {sentiment_data.get('sentiment')}.\n"
            f"Audience gender: {gender or 'unspecified'}, age group: {age_group or 'unspecified'}, "
            f"visual inspiration: {visual_style or 'neutral'}.\n\nOriginal transcript:\n{transcript}"
        )
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": "You are a world-class storyteller and video script writer."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.content[0].text.strip()
