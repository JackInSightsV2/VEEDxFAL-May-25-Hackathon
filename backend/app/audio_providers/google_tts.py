from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    from google.cloud import texttospeech  # type: ignore
except ImportError:  # pragma: no cover
    texttospeech = None

from ..logger import logger
from ..pipeline.interfaces import AudioService


@dataclass
class GoogleTextToSpeechService(AudioService):
    """Google Cloud Text-to-Speech wrapper."""

    language_code: str = "en-US"
    voice_name: Optional[str] = None
    speaking_rate: float = 1.0
    pitch: float = 0.0
    audio_encoding: texttospeech.AudioEncoding = texttospeech.AudioEncoding.MP3 if texttospeech else None

    def __post_init__(self) -> None:
        if texttospeech is None:
            raise ImportError("google-cloud-texttospeech not installed. Install with `pip install google-cloud-texttospeech`.")
        if self.audio_encoding is None:
            self.audio_encoding = texttospeech.AudioEncoding.MP3
        self._client = texttospeech.TextToSpeechClient()

    def synthesize(self, text: str, job_id: str, *, gender: Optional[str]) -> str:
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.voice_name,
            ssml_gender=(
                texttospeech.SsmlVoiceGender.FEMALE
                if (gender or "").lower() == "female"
                else texttospeech.SsmlVoiceGender.MALE
                if (gender or "").lower() == "male"
                else texttospeech.SsmlVoiceGender.NEUTRAL
            ),
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=self.audio_encoding,
            speaking_rate=self.speaking_rate,
            pitch=self.pitch,
        )
        synthesis_input = texttospeech.SynthesisInput(text=text)
        response = self._client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )

        audio_path = logger.get_job_file_path(job_id, "google_tts.mp3")
        with open(audio_path, "wb") as out_file:
            out_file.write(response.audio_content)
        logger.log_step(job_id, "AUDIO_GENERATION_SUCCESS", f"Google TTS audio saved to {audio_path}")
        return audio_path
