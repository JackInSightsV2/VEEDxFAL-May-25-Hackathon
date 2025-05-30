from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import PlainTextResponse

from .whisper_transcriber import transcribe_video
from .utils import beautify_transcript, extract_key_phrases
from .elevenlabs import generate_voice
from .fal import generate_videos_from_phrases, async_generate_videos_from_phrases, generate_video_from_image, generate_blog_avatar_video
from .video_assembler import create_final_video
from .logger import logger
from .openai_image import generate_image_with_openai

app = FastAPI()

STYLE_MAP = {
    "ghibli": "Studio Ghibli",
    "pixar": "Pixar",
    "anime": "Anime",
    "watercolor": "Watercolor",
    "cyberpunk": "Cyberpunk",
    "blog-female": "Blog (Female)",
    "blog-male": "Blog (Male)",
    "realistic": "Realistic"
}

@app.get("/")
async def root():
    """API root endpoint."""
    return {"message": "🎬 Video Generation API", "endpoints": ["/generate", "/logs", "/health"]}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "video-generation-api"}


@app.get("/logs", response_class=PlainTextResponse)
async def get_logs(lines: int = 50):
    """Get recent log entries."""
    try:
        with open("logs.txt", "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return "".join(recent_lines)
    except FileNotFoundError:
        return "No logs found."


@app.post("/generate")
async def generate(
    video: UploadFile, 
    mood: str = Form("Reflective"),
    gender: str = Form(None),
    age_group: str = Form(None),
    visual_style: str = Form(None)
):
    """Generate a quirky daily journal video from user's input video."""
    
    # Map frontend style to internal style string
    internal_style = STYLE_MAP.get(visual_style, visual_style)
    
    # Generate unique job ID and start logging
    job_id = logger.generate_job_id()
    logger.log_job_start(job_id, mood)
    logger.log_step(job_id, "USER_INPUT", f"gender={gender}, age_group={age_group}, visual_style={internal_style}")
    
    try:
        # Save uploaded video to job folder
        input_video_path = logger.get_job_file_path(job_id, "input_video.mp4")
        logger.log_step(job_id, "UPLOAD", f"Processing uploaded video: {video.filename}")
        with open(input_video_path, "wb") as f:
            f.write(await video.read())

        # Step 1: Transcribe the input video
        logger.log_step(job_id, "TRANSCRIPTION_START", "Starting video transcription...")
        transcript = transcribe_video(input_video_path, job_id)
        logger.log_transcription(job_id, transcript)
        
        # Step 2: Dummy transcript analysis (Sievedata disconnected)
        logger.log_step(job_id, "ANALYSIS_START", "Skipping transcript analysis (Sievedata disconnected)...")
        sieve = {"sentiment": "positive", "topics": ["sample topic"]}
        logger.log_analysis(job_id, sieve)
        
        # Step 3: Extract key phrases for video generation (up to 5 phrases)
        logger.log_step(job_id, "KEY_PHRASES_START", "Extracting key phrases...")
        key_phrases = extract_key_phrases(transcript, sieve, num_phrases=5, gender=gender, age_group=age_group, visual_style=internal_style)
        logger.log_key_phrases(job_id, key_phrases)
        
        # Step 4: Create a beautiful script for audio narration
        logger.log_step(job_id, "SCRIPT_CREATION", "Creating audio script...")
        script = beautify_transcript(transcript, mood, sieve, gender=gender, age_group=age_group, visual_style=internal_style)
        
        # Step 5: Generate audio narration
        logger.log_step(job_id, "AUDIO_START", "Generating audio narration...")
        audio_path = generate_voice(script, job_id)
        logger.log_audio_generation(job_id, script, audio_path)

        # Branch by style
        stylized = ["Studio Ghibli", "Pixar", "Anime", "Watercolor", "Cyberpunk"]
        if internal_style in stylized:
            # Generate images, then videos from images
            video_paths = []
            for i, phrase in enumerate(key_phrases):
                image_path = logger.get_job_file_path(job_id, f"openai_image_{i}.png")
                generate_image_with_openai(phrase, image_path)
                video_path = generate_video_from_image(image_path, phrase, i, job_id)
                video_paths.append(video_path)
        elif visual_style == "blog-female":
            # Use blog avatar video with any_female_primary
            video_path = generate_blog_avatar_video(script, "any_female_primary", 0, job_id)
            video_paths = [video_path]
        elif visual_style == "blog-male":
            # Use blog avatar video with any_male_primary
            video_path = generate_blog_avatar_video(script, "any_male_primary", 0, job_id)
            video_paths = [video_path]
        else:
            # Default/Realistic: use current async pipeline
            logger.log_video_generation_start(job_id, len(key_phrases))
            video_paths = await async_generate_videos_from_phrases(key_phrases, job_id)

        if not video_paths:
            error_msg = "Failed to generate any videos"
            logger.log_job_error(job_id, error_msg, "VIDEO_GENERATION")
            return {"error": error_msg, "job_id": job_id}
        
        # Step 7: Stitch videos together and add audio narration
        logger.log_step(job_id, "STITCHING_START", f"Stitching {len(video_paths)} videos together...")
        final_video_path = create_final_video(video_paths, audio_path, job_id)
        logger.log_video_stitching(job_id, video_paths, final_video_path)
        
        # Log job completion
        logger.log_job_complete(job_id, final_video_path, len(video_paths), len(key_phrases))

        return {
            "job_id": job_id,
            "video": final_video_path,
            "transcript": transcript,
            "key_phrases": key_phrases,
            "generated_videos": len(video_paths),
            "success_rate": f"{(len(video_paths)/len(key_phrases))*100:.1f}%" if key_phrases else "100%",
            "job_folder": logger.get_job_folder(job_id),
            "gender": gender,
            "age_group": age_group,
            "visual_style": internal_style
        }
        
    except Exception as e:
        logger.log_job_error(job_id, str(e), "PIPELINE")
        return {
            "error": f"Job failed: {str(e)}",
            "job_id": job_id
        }
