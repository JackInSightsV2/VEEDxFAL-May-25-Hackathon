from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

try:
    from google.cloud import language_v1  # type: ignore
except ImportError:  # pragma: no cover
    language_v1 = None

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class GoogleNLPAnalysisService(AnalysisService):
    """Google Cloud Natural Language API wrapper."""

    def __post_init__(self) -> None:
        if language_v1 is None:
            raise ImportError("google-cloud-language not installed. Install with `pip install google-cloud-language`.")

    def analyze(self, text: str) -> Dict[str, object]:
        client = language_v1.LanguageServiceClient()
        document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

        sentiment_response = client.analyze_sentiment(request={"document": document})
        sentiment = sentiment_response.document_sentiment
        sentiment_scores = {
            "score": sentiment.score if sentiment else None,
            "magnitude": sentiment.magnitude if sentiment else None,
        }
        sentiment_label = (
            "positive"
            if sentiment and sentiment.score > 0.25
            else "negative" if sentiment and sentiment.score < -0.25 else "neutral"
        )

        entities_response = client.analyze_entities(request={"document": document})
        entities = [
            {
                "name": entity.name,
                "type": language_v1.Entity.Type(entity.type_).name,
                "salience": entity.salience,
            }
            for entity in entities_response.entities
        ]

        classify_topics = []
        try:
            classification_response = client.classify_text(request={"document": document})
            classify_topics = [category.name for category in classification_response.categories]
        except Exception:
            # Classification requires certain text length; it's safe to ignore failures
            classify_topics = []

        return build_analysis_result(
            sentiment=sentiment_label,
            sentiment_scores=sentiment_scores,
            topics=classify_topics or [entity["name"] for entity in entities[:5]],
            language=sentiment_response.language if sentiment_response else None,
            entities=entities,
            raw={
                "sentiment": sentiment_response,
                "entities": entities_response.entities,
            },
        )
