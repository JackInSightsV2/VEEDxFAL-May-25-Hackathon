"""Transcription utilities using Whisper."""

import whisper


def transcribe_video(video_path: str) -> str:
    """Transcribe speech in the given video and return text."""
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    return result["text"]
