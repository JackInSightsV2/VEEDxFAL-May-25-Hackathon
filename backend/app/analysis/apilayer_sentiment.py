from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import requests

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class APILayerSentimentService(AnalysisService):
    """APILayer Sentiment Analysis wrapper."""

    api_key: Optional[str] = None
    endpoint: str = "https://api.apilayer.com/sentiment/analysis"

    def analyze(self, text: str) -> Dict[str, object]:
        headers = {"apikey": self.api_key or ""}
        if not headers["apikey"]:
            raise ValueError("APILayer Sentiment API key not provided.")
        response = requests.post(self.endpoint, headers=headers, json={"text": text}, timeout=30)
        response.raise_for_status()
        data = response.json()

        sentiment = data.get("sentiment")
        confidence = data.get("confidence")
        categories = data.get("categories", [])

        return build_analysis_result(
            sentiment=sentiment,
            sentiment_scores={"confidence": confidence},
            topics=categories,
            language=data.get("language"),
            raw=data,
        )
