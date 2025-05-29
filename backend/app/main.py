from fastapi import FastAPI, UploadFile, Form

from whisper_transcriber import transcribe_video
from sievedata import analyze_transcript
from utils import beautify_transcript
from elevenlabs import generate_voice
from fal import generate_image
from video_assembler import create_video

app = FastAPI()


@app.post("/generate")
async def generate(video: UploadFile, mood: str = Form("Reflective")):
    with open("input_video.mp4", "wb") as f:
        f.write(await video.read())

    transcript = transcribe_video("input_video.mp4")
    sieve = analyze_transcript(transcript)
    script = beautify_transcript(transcript, mood, sieve)
    audio_path = generate_voice(script)
    image_path = generate_image(script)
    video_path = create_video(image_path, audio_path)

    return {"video": video_path}
