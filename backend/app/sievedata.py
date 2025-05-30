import os
import requests

SIEVE_API_URL = "https://mango.sievedata.com/v2/push"
SIEVE_API_KEY = os.getenv("SIEVE_API_KEY", "demo-key-or-placeholder")


def transcribe_with_sievedata(audio_url: str, api_key: str = None) -> dict:
    """
    Call Sievedata API to transcribe an audio file from a URL.
    Returns the API response as a dict.
    """
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key or SIEVE_API_KEY,
    }
    payload = {
        "function": "sieve/transcribe",
        "inputs": {
            "file": {"url": audio_url},
            "backend": "stable-ts-whisper-large-v3-turbo",
            "word_level_timestamps": True,
            "source_language": "auto",
            "diarization_backend": "None",
            "min_speakers": -1,
            "max_speakers": -1,
            "custom_vocabulary": {},
            "translation_backend": "None",
            "target_language": "",
            "segmentation_backend": "ffmpeg-silence",
            "min_segment_length": -1,
            "min_silence_length": 0.4,
            "vad_threshold": 0.2,
            "pyannote_segmentation_threshold": 0.8,
            "chunks": [],
            "denoise_backend": "None",
            "initial_prompt": ""
        }
    }
    response = requests.post(SIEVE_API_URL, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

# This module is not currently used in the main project, but can be integrated later if needed. 