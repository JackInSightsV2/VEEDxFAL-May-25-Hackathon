"""Wrapper for Sievedata API calls."""

from __future__ import annotations

import os
import requests


def analyze_transcript(text: str) -> dict:
    """Analyze transcript text and return metadata from Sievedata."""
    headers = {"Authorization": f"Bearer {os.getenv('SIEVE_API_KEY')}"}
    payload = {"text": text}
    response = requests.post(
        "https://api.sievedata.com/analyze", json=payload, headers=headers
    )
    return response.json()
