from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import requests

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class MeaningCloudSentimentService(AnalysisService):
    """MeaningCloud sentiment analysis."""

    api_key: Optional[str] = None
    lang: str = "en"
    endpoint: str = "https://api.meaningcloud.com/sentiment-2.1"

    def _payload(self, text: str) -> Dict[str, str]:
        key = self.api_key or ""
        if not key:
            raise ValueError("MeaningCloud API key not provided.")
        return {
            "key": key,
            "txt": text,
            "lang": self.lang,
        }

    def analyze(self, text: str) -> Dict[str, object]:
        response = requests.post(self.endpoint, data=self._payload(text), timeout=30)
        response.raise_for_status()
        data = response.json()

        sentiment = data.get("score_tag", "NEU")
        sentiment_map = {
            "P+": "strong_positive",
            "P": "positive",
            "NEU": "neutral",
            "N": "negative",
            "N+": "strong_negative",
            "NONE": "none",
        }

        topics = [agreement.get("form") for agreement in data.get("entity_list", [])[:5]]

        return build_analysis_result(
            sentiment=sentiment_map.get(sentiment, "neutral"),
            sentiment_scores={"confidence": data.get("confidence")},
            topics=topics,
            language=data.get("lang"),
            raw=data,
        )


@dataclass
class MeaningCloudTopicsService(AnalysisService):
    """MeaningCloud topic extraction."""

    api_key: Optional[str] = None
    lang: str = "en"
    endpoint: str = "https://api.meaningcloud.com/topics-2.0"
    topic_type: str = "a"  # c=concepts, e=entities, a=all

    def _payload(self, text: str) -> Dict[str, str]:
        key = self.api_key or ""
        if not key:
            raise ValueError("MeaningCloud API key not provided.")
        return {
            "key": key,
            "txt": text,
            "lang": self.lang,
            "tt": self.topic_type,
        }

    def analyze(self, text: str) -> Dict[str, object]:
        response = requests.post(self.endpoint, data=self._payload(text), timeout=30)
        response.raise_for_status()
        data = response.json()

        concepts = [item["form"] for item in data.get("concept_list", [])]
        entities = [
            {"text": item["form"], "type": item.get("sementity", {}).get("type", "")}
            for item in data.get("entity_list", [])
        ]
        topics = concepts or [entity["text"] for entity in entities]

        return build_analysis_result(
            sentiment=None,
            topics=topics,
            language=data.get("lang"),
            entities=entities,
            raw=data,
        )
