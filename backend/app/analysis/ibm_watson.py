from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

try:
    from ibm_watson import NaturalLanguageUnderstandingV1  # type: ignore
    from ibm_cloud_sdk_core.authenticators import IAMAuthenticator  # type: ignore
    from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions, EmotionOptions, ConceptsOptions, EntitiesOptions, KeywordsOptions
except ImportError:  # pragma: no cover
    NaturalLanguageUnderstandingV1 = None

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class IBMWatsonNLUAnalysisService(AnalysisService):
    """IBM Watson Natural Language Understanding wrapper."""

    api_key: Optional[str] = None
    service_url: Optional[str] = None
    version: str = "2021-08-01"
    language: Optional[str] = None

    def __post_init__(self) -> None:
        if NaturalLanguageUnderstandingV1 is None:
            raise ImportError(
                "ibm-watson not installed. Install with `pip install ibm-watson`."
            )
        if not self.api_key or not self.service_url:
            raise ValueError("IBM Watson NLU requires api_key and service_url.")
        authenticator = IAMAuthenticator(self.api_key)
        self._client = NaturalLanguageUnderstandingV1(version=self.version, authenticator=authenticator)
        self._client.set_service_url(self.service_url)

    def analyze(self, text: str) -> Dict[str, object]:
        features = Features(
            sentiment=SentimentOptions(),
            emotion=EmotionOptions(),
            concepts=ConceptsOptions(limit=5),
            entities=EntitiesOptions(limit=10, sentiment=True, emotion=True),
            keywords=KeywordsOptions(limit=10, sentiment=True),
        )
        response = self._client.analyze(text=text, features=features, language=self.language).get_result()

        sentiment = response.get("sentiment", {}).get("document", {}).get("label")
        sentiment_scores = response.get("sentiment", {}).get("document", {}).get("score")
        keywords = [kw["text"] for kw in response.get("keywords", [])]
        concepts = [concept["text"] for concept in response.get("concepts", [])]
        topics = keywords or concepts

        entities = [
            {
                "text": entity.get("text"),
                "type": entity.get("type"),
                "relevance": entity.get("relevance"),
                "sentiment": entity.get("sentiment"),
                "emotion": entity.get("emotion"),
            }
            for entity in response.get("entities", [])
        ]

        return build_analysis_result(
            sentiment=sentiment,
            sentiment_scores={"score": sentiment_scores},
            topics=topics,
            language=response.get("language"),
            entities=entities,
            raw=response,
        )
