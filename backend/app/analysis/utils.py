from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


def build_analysis_result(
    *,
    sentiment: Optional[str],
    topics: Optional[Iterable[str]] = None,
    sentiment_scores: Optional[Dict[str, Any]] = None,
    language: Optional[str] = None,
    entities: Optional[Iterable[Dict[str, Any]]] = None,
    raw: Optional[Dict[str, Any]] = None,
    translated_text: Optional[str] = None,
    **extras: Any,
) -> Dict[str, Any]:
    """Normalize analysis output for pipeline consumption."""

    return {
        "sentiment": sentiment,
        "sentiment_scores": sentiment_scores or {},
        "topics": list(topics or []),
        "language": language,
        "entities": list(entities or []),
        "translated_text": translated_text,
        "raw": raw or {},
        **extras,
    }
