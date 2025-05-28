# 🧠 AI Memory Journal

**Tagline:** *“Turn your day into a narrated, cinematic story.”*

## 📘 Overview

AI Memory Journal is a web-based tool that transforms a short personal selfie video into a cinematic memory recap. Powered by state-of-the-art AI services, it transcribes your voice, analyzes your tone, rewrites it beautifully, adds narration, and layers visuals and music — producing a poetic, stylized story of your day.

Built in just 2 days for a hackathon using:

* [Veed AI](https://www.veed.io/)
* [Fal AI](https://fal.ai/)
* [ElevenLabs](https://elevenlabs.io/)
* [Sievedata AI](https://sievedata.com/)

---

## 🌟 Goals

* Enable users to reflect creatively on their lives
* Leverage multimodal AI (audio + vision + language)
* Produce short, emotionally resonant video journals
* Create a clean MVP with strong demo value

---

## 🛠️ Tech Stack

| Purpose                  | Tool/Service       |
| ------------------------ | ------------------ |
| Frontend UI              | Bolt.new           |
| Backend Framework        | FastAPI (Python)   |
| Speech-to-Text           | OpenAI Whisper     |
| Semantic Analysis & Tags | **Sievedata AI**   |
| Visual Generation        | **Fal AI**         |
| Voice Generation         | **ElevenLabs**     |
| Video Rendering          | ffmpeg / VEED API  |
| File Upload              | Local / Cloudinary |

---

## 🧩 System Architecture

```
[Bolt Frontend]
      |
[User Uploads Video + Mood]
      |
[FastAPI Backend]
  |        |         |         |
[Whisper] [Sievedata] [Fal AI] [ElevenLabs]
      \       |        |        /
       \---->[Script + Assets]
              |
       [ffmpeg / VEED Assembly]
              |
      [Final Video Output (.mp4)]
```

---

## 📲 User Flow

1. 📅 **Upload**
   User uploads a selfie video and selects a mood (e.g. "Reflective").

2. 🎧 **Transcription**
   Whisper converts speech in the video to text.

3. 🧠 **Semantic Enrichment (Sievedata)**
   Extracts emotion, themes, and key entities to enhance storytelling.

4. ✍️ **Script Beautification**
   Converts transcript into poetic narration based on mood and Sieve metadata.

5. 🎤 **Voice-Over (ElevenLabs)**
   Narrates the story with a realistic AI voice.

6. 🖼️ **Visual Generation (Fal AI)**
   Creates a thematic image or visual scene to accompany narration.

7. 🎬 **Assembly**
   Uses ffmpeg or VEED to produce the final cinematic video, complete with narration, music, and visuals.

8. 🎮 **Output**
   User can preview or download their finished memory journal video.

---

## 💡 Stretch Goals

* Weekly Recap Compilation
* Multiple voice style options
* Mood-based background music
* Video search via Sieve metadata tags

---

## ✨ Why It Stands Out

* Emotionally engaging and relatable use case
* Viral-ready video output with real user value
* End-to-end integration of powerful AI services
* Impressively polished MVP built in under 48 hours

---

## 🧪 Try It (Coming Soon)

> \[Live demo link or HuggingFace Space here]

---

## 🤝 Team

**Built for VEED x FAL May-25 Hackathon by JackInSights**
