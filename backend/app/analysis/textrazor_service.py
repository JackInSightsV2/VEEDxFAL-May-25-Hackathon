from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

try:
    import textrazor  # type: ignore
except ImportError:  # pragma: no cover
    textrazor = None

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class TextRazorAnalysisService(AnalysisService):
    """TextRazor topic/entity extraction."""

    api_key: Optional[str] = None
    extractors: str = "topics,entities,entailments"

    def __post_init__(self) -> None:
        if textrazor is None:
            raise ImportError("textrazor not installed. Install with `pip install textrazor`.")
        if not self.api_key:
            raise ValueError("TextRazor API key must be provided.")
        textrazor.api_key = self.api_key

    def analyze(self, text: str) -> Dict[str, object]:
        client = textrazor.TextRazor(extractors=self.extractors)
        response = client.analyze(text)

        topics = [topic.label for topic in response.topics()] if response.topics() else []
        entities = [
            {"text": entity.matched_text, "type": entity.type, "relevance": entity.relevance_score}
            for entity in response.entities()
        ]

        sentiment = None
        sentiment_scores = {}
        if response.ok:
            doc_sentiment = response.sentences()[0].sentiment_score if response.sentences() else None
            if doc_sentiment is not None:
                sentiment = "positive" if doc_sentiment > 0 else "negative" if doc_sentiment < 0 else "neutral"
                sentiment_scores = {"score": doc_sentiment}

        return build_analysis_result(
            sentiment=sentiment,
            sentiment_scores=sentiment_scores,
            topics=topics,
            entities=entities,
            raw=response.response,
        )
