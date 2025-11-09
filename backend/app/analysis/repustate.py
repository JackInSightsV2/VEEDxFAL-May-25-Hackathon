from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import requests

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class RepustateSentimentService(AnalysisService):
    """Repustate sentiment analysis API."""

    api_key: Optional[str] = None
    base_url: str = "https://api.repustate.com/v4"
    language: str = "en"

    def _url(self) -> str:
        key = self.api_key or ""
        if not key:
            raise ValueError("Repustate API key not provided.")
        return f"{self.base_url}/{key}/sentiment.json"

    def analyze(self, text: str) -> Dict[str, object]:
        response = requests.post(self._url(), data={"text": text, "lang": self.language}, timeout=30)
        response.raise_for_status()
        data = response.json()

        sentiment = data.get("result", {}).get("label")
        score = data.get("result", {}).get("score")
        keywords = data.get("result", {}).get("topics", [])

        return build_analysis_result(
            sentiment=sentiment,
            sentiment_scores={"score": score},
            topics=keywords,
            language=self.language,
            raw=data,
        )
