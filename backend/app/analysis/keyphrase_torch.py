from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import List, Optional

import torch

from ..pipeline.interfaces import KeyPhraseService


@dataclass
class TorchKeyPhraseService(KeyPhraseService):
    """Lightweight PyTorch-based key phrase scorer.

    The model computes a handcrafted feature vector per sentence and
    uses a small feed-forward network to estimate importance scores.
    """

    num_phrases: int = 5
    min_tokens: int = 3

    def __post_init__(self) -> None:
        self._weights = torch.tensor([[0.4, 0.3, 0.2, 0.1]], dtype=torch.float32)
        self._bias = torch.tensor([0.05], dtype=torch.float32)

    def _split_sentences(self, text: str) -> List[str]:
        sentences = re.split(r"[.!?]+", text)
        return [sentence.strip() for sentence in sentences if sentence.strip()]

    def _sentence_features(self, sentence: str) -> torch.Tensor:
        tokens = sentence.split()
        token_count = len(tokens)
        if token_count == 0:
            return torch.zeros(4)

        avg_token_length = sum(len(token) for token in tokens) / token_count
        capital_ratio = sum(1 for token in tokens if token[:1].isupper()) / token_count
        contains_number = any(any(char.isdigit() for char in token) for token in tokens)

        features = torch.tensor(
            [
                math.log(1 + token_count),
                avg_token_length / 10.0,
                capital_ratio,
                1.0 if contains_number else 0.0,
            ],
            dtype=torch.float32,
        )
        return features

    def extract(
        self,
        text: str,
        sentiment_data: dict,
        *,
        num_phrases: int,
        gender: Optional[str],
        age_group: Optional[str],
        visual_style: Optional[str],
    ) -> List[str]:
        sentences = self._split_sentences(text)
        if not sentences:
            return [text.strip()]

        scores = []
        for sentence in sentences:
            tokens = sentence.split()
            if len(tokens) < self.min_tokens:
                continue
            features = self._sentence_features(sentence)
            raw_score = torch.sigmoid(self._weights @ features + self._bias).item()
            # Boost score if sentiment topics mention keywords present in sentence
            topics = sentiment_data.get("topics", [])
            topic_boost = any(topic.lower() in sentence.lower() for topic in topics)
            if topic_boost:
                raw_score += 0.1
            scores.append((raw_score, sentence))

        if not scores:
            return [text.strip()]

        scores.sort(key=lambda item: item[0], reverse=True)
        selected = [sentence for _, sentence in scores[: num_phrases or self.num_phrases]]
        return selected
