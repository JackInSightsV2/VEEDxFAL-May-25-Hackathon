"""AWS Translate + Comprehend integration as a drop-in analysis service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from .pipeline.interfaces import AnalysisService


class AWSTranslateError(RuntimeError):
    """Raised when AWS language services fail."""


def _get_region(region: Optional[str]) -> str:
    return region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"


def _detect_language(comprehend_client, text: str) -> str:
    response = comprehend_client.detect_dominant_language(Text=text)
    languages = response.get("Languages", [])
    if not languages:
        raise AWSTranslateError("Unable to detect language for input text.")
    # Highest score first
    languages.sort(key=lambda item: item.get("Score", 0), reverse=True)
    return languages[0].get("LanguageCode", "en")


def analyze_with_aws(
    text: str,
    *,
    target_language: str = "en",
    source_language: Optional[str] = None,
    region: Optional[str] = None,
    sentiment_language: Optional[str] = None,
) -> Dict[str, object]:
    """Run translation + sentiment/key-phrase analysis using AWS services."""

    region_name = _get_region(region)
    comprehend = boto3.client("comprehend", region_name=region_name)
    translate = boto3.client("translate", region_name=region_name)

    if not source_language:
        source_language = _detect_language(comprehend, text)

    if sentiment_language:
        sentiment_lang = sentiment_language
    else:
        sentiment_lang = source_language if source_language != "auto" else "en"

    translated_text = text
    translation_applied = False
    if source_language.lower() != target_language.lower():
        translation_response = translate.translate_text(
            Text=text,
            SourceLanguageCode=source_language,
            TargetLanguageCode=target_language,
        )
        translated_text = translation_response.get("TranslatedText", text)
        translation_applied = True

    sentiment_response = comprehend.detect_sentiment(
        Text=translated_text if translation_applied else text,
        LanguageCode=sentiment_lang if translation_applied else source_language,
    )
    sentiment = sentiment_response.get("Sentiment", "NEUTRAL").lower()
    sentiment_scores = sentiment_response.get("SentimentScore", {})

    key_phrase_response = comprehend.detect_key_phrases(
        Text=translated_text if translation_applied else text,
        LanguageCode=sentiment_lang if translation_applied else source_language,
    )
    key_phrases = [
        phrase.get("Text")
        for phrase in key_phrase_response.get("KeyPhrases", [])
        if phrase.get("Text")
    ]

    return {
        "sentiment": sentiment,
        "sentiment_scores": sentiment_scores,
        "topics": key_phrases[:10],
        "language": source_language,
        "translated": translation_applied,
        "translated_text": translated_text if translation_applied else None,
    }


@dataclass
class AWSTranslateAnalysisService(AnalysisService):
    """AnalysisService using AWS Translate + Comprehend."""

    target_language: str = "en"
    region: Optional[str] = None

    def analyze(self, text: str) -> Dict[str, object]:
        try:
            return analyze_with_aws(
                text,
                target_language=self.target_language,
                region=self.region,
            )
        except (BotoCoreError, ClientError) as boto_err:
            raise AWSTranslateError(f"AWS language service error: {boto_err}") from boto_err


__all__ = [
    "AWSTranslateAnalysisService",
    "analyze_with_aws",
    "AWSTranslateError",
]
