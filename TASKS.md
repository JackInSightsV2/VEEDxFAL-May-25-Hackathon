# ✅ AI Memory Journal — Development Task List

This file outlines all the tasks needed to build the backend for the AI Memory Journal project. Each task is broken down into atomic units that can be fed into AI code assistants like Cursor AI or Copilot.

---

## 📁 Project Setup

* [x] Create a Python project folder with the following structure:

  ```bash
  mkdir backend && cd backend
  touch main.py fal.py elevenlabs.py video_assembler.py envloader.py whisper_transcriber.py sievedata.py requirements.txt .env
  ```

* [x] Initialize a virtual environment and install dependencies:

  ```bash
  python -m venv venv
  source venv/bin/activate
  pip install fastapi uvicorn requests python-dotenv openai-whisper ffmpeg-python
  ```

* [x] Add `.env` support:

  ```python
  # envloader.py
  from dotenv import load_dotenv
  import os
  load_dotenv()

  ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
  FAL_API_KEY = os.getenv("FAL_API_KEY")
  SIEVE_API_KEY = os.getenv("SIEVE_API_KEY")
  ```

---

## 🔑 API Key Setup (`.env`)

* [x] Add the following to your `.env` file:

  ```env
  ELEVEN_API_KEY=your_elevenlabs_key
  FAL_API_KEY=your_fal_key
  SIEVE_API_KEY=your_sievedata_key
  ```

---

## 📥 Upload Endpoint (`main.py`)

* [x] Setup FastAPI with an upload route:

  ```python
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
  ```

---

## 🔊 Transcription (`whisper_transcriber.py`)

* [x] Use OpenAI Whisper:

  ```python
  import whisper

  def transcribe_video(video_path):
      model = whisper.load_model("base")
      result = model.transcribe(video_path)
      return result['text']
  ```

---

## 🧠 Sieve Integration (`sievedata.py`)

* [x] Use Sievedata API to analyze transcript:

  ```python
  import requests
  import os

  def analyze_transcript(text):
      headers = {"Authorization": f"Bearer {os.getenv('SIEVE_API_KEY')}"}
      payload = {"text": text}
      response = requests.post("https://api.sievedata.com/analyze", json=payload, headers=headers)
      return response.json()
  ```

---

## ✍️ Script Beautifier (`utils.py`)

* Beautify transcript using simple formatting:

  ```python
  def beautify_transcript(transcript, mood, sieve_data):
      themes = ", ".join(sieve_data.get("topics", []))
      sentiment = sieve_data.get("sentiment", "reflective")
      return f"A {sentiment} retelling of a day themed around {themes}:\n\n{transcript}"
  ```

---

## 🖼️ Visual Generation (`fal.py`)

* Generate image using Fal AI:

  ```python
  import requests
  import os

  def generate_image(prompt):
      headers = {"Authorization": f"Bearer {os.getenv('FAL_API_KEY')}"}
      payload = {"prompt": prompt, "num_images": 1}
      response = requests.post("https://api.fal.ai/generate", json=payload, headers=headers)
      image_url = response.json()["images"][0]
      image_path = "output.jpg"
      with open(image_path, "wb") as f:
          f.write(requests.get(image_url).content)
      return image_path
  ```

---

## 🎙️ Voice Generation (`elevenlabs.py`)

* Generate voice from script:

  ```python
  import requests
  import os

  def generate_voice(script, voice_id="Rachel"):
      headers = {
          "xi-api-key": os.getenv("ELEVEN_API_KEY"),
          "Content-Type": "application/json"
      }
      payload = {
          "text": script,
          "voice_settings": {"stability": 0.7, "similarity_boost": 0.8}
      }
      response = requests.post(
          f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream",
          headers=headers,
          json=payload
      )
      with open("voice.mp3", "wb") as f:
          f.write(response.content)
      return "voice.mp3"
  ```

---

## 🎬 Video Assembly (`video_assembler.py`)

* Use ffmpeg to combine image and narration:

  ```python
  import subprocess

  def create_video(image_path, audio_path, output_path="final.mp4"):
      subprocess.run([
          "ffmpeg", "-y",
          "-loop", "1", "-i", image_path,
          "-i", audio_path,
          "-c:v", "libx264", "-tune", "stillimage",
          "-shortest", "-pix_fmt", "yuv420p", output_path
      ])
      return output_path
  ```

---

## 🧪 Curl Test Example

```bash
curl -X POST \
  -F "video=@/path/to/video.mp4" \
  -F "mood=Reflective" \
  http://localhost:8000/generate
```

---

## 📦 Final Delivery

* Push code to GitHub with README.md
* Include example input and output video for demo
* Deploy to Replit, HuggingFace Spaces, or Render
