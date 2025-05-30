"""Wrapper for Sievedata API calls."""

from __future__ import annotations

import os
import requests
from google.cloud import language_v1


def analyze_transcript(text: str) -> dict:
    """Analyze transcript text and return sentiment and topics using Google Cloud Natural Language API."""
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)

    # Sentiment analysis
    sentiment_response = client.analyze_sentiment(request={"document": document})
    sentiment_score = sentiment_response.document_sentiment.score
    # Map score to a label (optional, you can adjust this mapping)
    if sentiment_score > 0.25:
        sentiment = "positive"
    elif sentiment_score < -0.25:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Entity analysis (topics)
    entity_response = client.analyze_entities(request={"document": document})
    topics = list({entity.name for entity in entity_response.entities if entity.type_ != language_v1.Entity.Type.NUMBER})

    return {"sentiment": sentiment, "topics": topics}
