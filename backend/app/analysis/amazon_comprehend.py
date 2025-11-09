from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class AmazonComprehendAnalysisService(AnalysisService):
    """Amazon Comprehend sentiment + key phrase extraction."""

    region_name: Optional[str] = None
    language_code: str = "en"

    def _client(self):
        return boto3.client("comprehend", region_name=self.region_name)

    def analyze(self, text: str) -> Dict[str, object]:
        client = self._client()
        try:
            sentiment_response = client.detect_sentiment(Text=text, LanguageCode=self.language_code)
            key_phrase_response = client.detect_key_phrases(Text=text, LanguageCode=self.language_code)
            entities_response = client.detect_entities(Text=text, LanguageCode=self.language_code)
        except (BotoCoreError, ClientError) as error:
            raise RuntimeError(f"Amazon Comprehend error: {error}") from error

        sentiment = sentiment_response.get("Sentiment", "").lower()
        sentiment_scores = sentiment_response.get("SentimentScore", {})
        key_phrases = [phrase["Text"] for phrase in key_phrase_response.get("KeyPhrases", [])]
        entities = [
            {"text": entity["Text"], "type": entity["Type"], "score": entity["Score"]}
            for entity in entities_response.get("Entities", [])
        ]

        return build_analysis_result(
            sentiment=sentiment,
            sentiment_scores=sentiment_scores,
            topics=key_phrases,
            language=self.language_code,
            entities=entities,
            raw={
                "sentiment": sentiment_response,
                "key_phrases": key_phrase_response,
                "entities": entities_response,
            },
        )
