"""Transcription utilities using Whisper."""

from google.cloud import speech
import os
from .logger import logger


def transcribe_video(video_path: str, job_id: str = None) -> str:
    # Set Google credentials (if not already set)
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        # Assumes the JSON key is in the project root
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_path = os.path.join(root_dir, "veedxfal-hackathon-2025-ea1537c41d2c.json")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

    # Convert video to audio (WAV) for Google STT
    if job_id:
        audio_path = logger.get_job_file_path(job_id, "temp_audio.wav")
    else:
        audio_path = "temp_audio.wav"
    
    os.system(f'ffmpeg -y -i "{video_path}" -ar 16000 -ac 1 -f wav "{audio_path}"')

    client = speech.SpeechClient()
    with open(audio_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)
    transcript = " ".join([result.alternatives[0].transcript for result in response.results])
    return transcript
