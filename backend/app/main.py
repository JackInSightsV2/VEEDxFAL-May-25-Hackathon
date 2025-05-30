from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import PlainTextResponse

from .whisper_transcriber import transcribe_video
from .sievedata import analyze_transcript
from .utils import beautify_transcript, extract_key_phrases
from .elevenlabs import generate_voice
from .fal import generate_videos_from_phrases
from .video_assembler import create_final_video
from .logger import logger

app = FastAPI()


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
async def generate(video: UploadFile, mood: str = Form("Reflective")):
    """Generate a quirky daily journal video from user's input video."""
    
    # Generate unique job ID and start logging
    job_id = logger.generate_job_id()
    logger.log_job_start(job_id, mood)
    
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
        
        # Step 2: Analyze transcript for sentiment and topics
        logger.log_step(job_id, "ANALYSIS_START", "Starting transcript analysis...")
        sieve = analyze_transcript(transcript)
        logger.log_analysis(job_id, sieve)
        
        # Step 3: Extract key phrases for video generation (3-4 phrases)
        logger.log_step(job_id, "KEY_PHRASES_START", "Extracting key phrases...")
        key_phrases = extract_key_phrases(transcript, sieve, num_phrases=4)
        logger.log_key_phrases(job_id, key_phrases)
        
        # Step 4: Create a beautiful script for audio narration
        logger.log_step(job_id, "SCRIPT_CREATION", "Creating audio script...")
        script = beautify_transcript(transcript, mood, sieve)
        
        # Step 5: Generate audio narration
        logger.log_step(job_id, "AUDIO_START", "Generating audio narration...")
        audio_path = generate_voice(script, job_id)
        logger.log_audio_generation(job_id, script, audio_path)
        
        # Step 6: Generate videos for each key phrase
        logger.log_video_generation_start(job_id, len(key_phrases))
        video_paths = generate_videos_from_phrases(key_phrases, job_id)
        
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
            "success_rate": f"{(len(video_paths)/len(key_phrases))*100:.1f}%",
            "job_folder": logger.get_job_folder(job_id)
        }
        
    except Exception as e:
        logger.log_job_error(job_id, str(e), "PIPELINE")
        return {
            "error": f"Job failed: {str(e)}",
            "job_id": job_id
        }
