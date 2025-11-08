from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import azure.cognitiveservices.speech as speechsdk  # type: ignore
except ImportError:  # pragma: no cover
    speechsdk = None

from ..logger import logger
from ..pipeline.interfaces import TranscriptionService
from .utils import extract_audio_from_media


@dataclass
class AzureSpeechTranscriptionService(TranscriptionService):
    """Transcribe audio using Microsoft Azure Speech-to-Text."""

    subscription_key: Optional[str] = None
    region: Optional[str] = None
    language: str = "en-US"

    def _config(self):
        if speechsdk is None:
            raise ImportError(
                "azure-cognitiveservices-speech not installed. Install with `pip install azure-cognitiveservices-speech`."
            )
        key = self.subscription_key or speechsdk.SpeechConfig.get_subscription()
        region = self.region or speechsdk.SpeechConfig.get_region()
        if not key or not region:
            raise ValueError("Azure Speech subscription key and region must be provided.")
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_recognition_language = self.language
        return speech_config

    def transcribe(self, video_path: str, job_id: str) -> str:
        audio_path = extract_audio_from_media(video_path, job_id, format="wav")
        logger.log_step(job_id, "TRANSCRIPTION_AZURE", "Submitting audio to Azure Speech service")
        speech_config = self._config()
        audio_config = speechsdk.audio.AudioConfig(filename=audio_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = result.text or ""
            logger.log_step(job_id, "TRANSCRIPTION_COMPLETE", f"Azure STT produced {len(text)} characters")
            return text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            raise RuntimeError(f"Azure STT could not recognize speech in {audio_path}")
        else:
            raise RuntimeError(f"Azure STT error: {result.reason} - {result.cancellation_details}")
