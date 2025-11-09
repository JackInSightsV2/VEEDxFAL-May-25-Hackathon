from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

try:
    from azure.ai.textanalytics import (
        TextAnalyticsClient,
        AzureKeyCredential,
    )  # type: ignore
except ImportError:  # pragma: no cover
    TextAnalyticsClient = None

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class AzureLanguageAnalysisService(AnalysisService):
    """Microsoft Azure Text Analytics wrapper."""

    endpoint: str = ""
    api_key: Optional[str] = None
    language: Optional[str] = None

    def __post_init__(self) -> None:
        if TextAnalyticsClient is None:
            raise ImportError(
                "azure-ai-textanalytics not installed. Install with `pip install azure-ai-textanalytics`."
            )
        if not self.endpoint:
            raise ValueError("Azure Text Analytics endpoint must be provided.")
        if not self.api_key:
            raise ValueError("Azure Text Analytics API key must be provided.")
        self._client = TextAnalyticsClient(endpoint=self.endpoint, credential=AzureKeyCredential(self.api_key))

    def analyze(self, text: str) -> Dict[str, object]:
        documents = [{"id": "1", "text": text, "language": self.language}] if self.language else [{"id": "1", "text": text}]

        sentiment_result = self._client.analyze_sentiment(documents)[0]
        sentiment = sentiment_result.sentiment
        sentiment_scores = {
            "positive": sentiment_result.confidence_scores.positive,
            "neutral": sentiment_result.confidence_scores.neutral,
            "negative": sentiment_result.confidence_scores.negative,
        }

        key_phrase_result = self._client.extract_key_phrases(documents)[0]
        key_phrases = key_phrase_result.key_phrases

        entity_result = self._client.recognize_entities(documents)[0]
        entities = [
            {"text": entity.text, "category": entity.category, "subcategory": entity.subcategory, "confidence": entity.confidence_score}
            for entity in entity_result.entities
        ]

        return build_analysis_result(
            sentiment=sentiment,
            sentiment_scores=sentiment_scores,
            topics=key_phrases,
            language=self.language,
            entities=entities,
            raw={
                "sentiment": sentiment_result.as_dict(),
                "key_phrases": key_phrase_result.as_dict(),
                "entities": entity_result.as_dict(),
            },
        )
