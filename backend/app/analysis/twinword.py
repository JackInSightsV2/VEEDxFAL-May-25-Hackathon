from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import requests

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class TwinwordSentimentService(AnalysisService):
    """Twinword sentiment API wrapper."""

    api_key: Optional[str] = None
    endpoint: str = "https://api.twinword.com/api/v7/sentiment/analyze/"

    def analyze(self, text: str) -> Dict[str, object]:
        headers = {"X-Twaip-Key": self.api_key or ""}
        if not headers["X-Twaip-Key"]:
            raise ValueError("Twinword API key not provided.")

        response = requests.post(self.endpoint, headers=headers, data={"text": text}, timeout=30)
        response.raise_for_status()
        data = response.json()

        sentiment = data.get("type")
        score = data.get("score")
        keywords = data.get("keyword", [])

        return build_analysis_result(
            sentiment=sentiment,
            sentiment_scores={"score": score},
            topics=keywords,
            language=data.get("lang_code"),
            raw=data,
        )
