from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None

from ..pipeline.interfaces import ScriptService


@dataclass
class OpenAIScriptService(ScriptService):
    """Script generation using OpenAI GPT models."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 800
    system_prompt: str = "You are a creative director crafting engaging video scripts."

    def _client(self):
        if OpenAI is None:
            raise ImportError("openai package not installed. Install with `pip install openai`.")
        return OpenAI()

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
        client = self._client()
        prompt = (
            "Summarize and restructure the following diary-style transcript into a concise, engaging script. "
            f"Adopt a {mood.lower()} tone and match the sentiment summary {sentiment_data.get('sentiment')}.\n\n"
            f"Audience gender: {gender or 'unspecified'}, age group: {age_group or 'unspecified'}, "
            f"visual style cue: {visual_style or 'neutral'}.\n\nTranscript:\n{transcript}"
        )
        response = client.responses.create(
            model=self.model,
            input=prompt,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            system_prompt=self.system_prompt,
        )
        text = response.output_text if hasattr(response, "output_text") else response.data[0].text
        return text.strip()
