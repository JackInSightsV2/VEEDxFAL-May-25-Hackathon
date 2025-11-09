from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import azure.cognitiveservices.speech as speechsdk  # type: ignore
except ImportError:  # pragma: no cover
    speechsdk = None

from ..logger import logger
from ..pipeline.interfaces import AudioService


@dataclass
class AzureSpeechTTSService(AudioService):
    """Azure Speech Service text-to-speech integration."""

    subscription_key: Optional[str] = None
    region: Optional[str] = None
    voice_name: str = "en-US-JennyNeural"
    output_format: str = "audio-16khz-32kbitrate-mono-mp3"

    def _speech_config(self):
        if speechsdk is None:
            raise ImportError("azure-cognitiveservices-speech not installed. Install with `pip install azure-cognitiveservices-speech`.")
        key = self.subscription_key or speechsdk.SpeechConfig.get_subscription()
        region = self.region or speechsdk.SpeechConfig.get_region()
        if not key or not region:
            raise ValueError("Azure Speech subscription key and region are required.")
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_synthesis_voice_name = self.voice_name
        speech_config.set_speech_synthesis_output_format(
            getattr(speechsdk.SpeechSynthesisOutputFormat, self.output_format.replace("-", "_").upper(), speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3)
        )
        return speech_config

    def synthesize(self, text: str, job_id: str, *, gender: Optional[str]) -> str:
        speech_config = self._speech_config()
        audio_path = logger.get_job_file_path(job_id, "azure_tts.mp3")
        audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_path)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = synthesizer.speak_text_async(text).get()
        if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
            raise RuntimeError(f"Azure Speech synthesis failed: {result.cancellation_details if hasattr(result, 'cancellation_details') else result.reason}")
        logger.log_step(job_id, "AUDIO_GENERATION_SUCCESS", f"Azure TTS audio saved to {audio_path}")
        return audio_path
