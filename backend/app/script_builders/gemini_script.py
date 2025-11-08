from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover
    genai = None

from ..pipeline.interfaces import ScriptService


@dataclass
class GeminiScriptService(ScriptService):
    """Script generation using Google Gemini."""

    api_key: Optional[str] = None
    model: str = "gemini-1.5-flash"
    temperature: float = 0.7

    def __post_init__(self) -> None:
        if genai is None:
            raise ImportError("google-generativeai not installed. Install with `pip install google-generativeai`.")
        if not self.api_key:
            raise ValueError("Gemini API key must be provided.")
        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model)

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
            f"Rewrite the following transcript into a script suitable for a {mood.lower()} short-form narrative video.\n"
            f"Sentiment: {sentiment_data.get('sentiment')}. Audience gender: {gender or 'unspecified'}, "
            f"age group: {age_group or 'unspecified'}. Visual style: {visual_style or 'neutral'}.\n\n"
            f"Transcript:\n{transcript}"
        )
        response = self._model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=900,
            ),
        )
        return response.text.strip()
