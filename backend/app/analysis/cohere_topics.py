from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

try:
    import cohere  # type: ignore
except ImportError:  # pragma: no cover
    cohere = None

from ..pipeline.interfaces import AnalysisService
from .utils import build_analysis_result


@dataclass
class CohereTopicExtractionService(AnalysisService):
    """Cohere Topic Extraction API wrapper."""

    api_key: Optional[str] = None
    model: str = "embed-multilingual-v3.0"
    num_topics: int = 5

    def __post_init__(self) -> None:
        if cohere is None:
            raise ImportError("cohere not installed. Install with `pip install cohere`.")
        if not self.api_key:
            raise ValueError("Cohere API key must be provided.")
        self._client = cohere.Client(self.api_key)

    def analyze(self, text: str) -> Dict[str, object]:
        response = self._client.analyze_texts(
            texts=[text],
            dataset_type="generic",
            feature_types=["topics"],
            model=self.model,
        )
        topics = []
        entities = []
        if response.results:
            result = response.results[0]
            for topic in result.topics[: self.num_topics]:
                topics.append(topic.labels[0] if topic.labels else topic.name)
                entities.append({"topic": topic.name, "confidence": topic.confidence})

        return build_analysis_result(
            sentiment=None,
            topics=topics,
            entities=entities,
            raw=response.to_dict(),
        )
