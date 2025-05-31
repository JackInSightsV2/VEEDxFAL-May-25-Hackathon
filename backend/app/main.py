from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import PlainTextResponse
import asyncio
import time
import os

from .whisper_transcriber import transcribe_video
from .utils import beautify_transcript, extract_key_phrases
from .elevenlabs import generate_voice
from .fal import generate_videos_from_phrases, async_generate_videos_from_phrases, generate_video_from_image, generate_blog_avatar_video, async_generate_video_from_image
from .video_assembler import create_final_video
from .logger import logger
from .openai_image import generate_image_with_openai, async_generate_image_with_openai
from .gcp_nlp import analyze_transcript
from .piwigo_uploader import upload_image
from video_utils import get_video_duration
from video_stitcher import stitch_videos

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
    return {
        "message": "🎬 Video Generation API (ASYNC Processing)", 
        "endpoints": [
            {
                "path": "/generate", 
                "method": "POST",
                "description": "Generate video from uploaded video file using ASYNC concurrent processing",
                "parameters": ["video (file)", "mood", "gender", "age_group", "visual_style", "voice_style"],
                "processing": "ASYNC (concurrent images & videos)"
            },
            {
                "path": "/generate-from-text", 
                "method": "POST", 
                "description": "Generate video directly from text using ASYNC concurrent processing (no upload required)",
                "parameters": ["text", "mood", "gender", "age_group", "visual_style", "voice_style"],
                "processing": "ASYNC (concurrent images & videos)"
            },
            {
                "path": "/logs", 
                "method": "GET", 
                "description": "Get recent log entries"
            },
            {
                "path": "/health", 
                "method": "GET", 
                "description": "Health check"
            },
            {
                "path": "/text-to-blog",
                "method": "POST",
                "description": "Generate a 25-second talking avatar video from text input using blog avatars.",
                "parameters": ["text", "name", "gender", "age_group", "mood", "voice_style"],
                "processing": "ASYNC"
            }
        ],
        "supported_styles": [
            "Studio Ghibli", "Pixar", "Anime", "Watercolor", "Cyberpunk", 
            "blog-female", "blog-male", "Realistic"
        ],
        "supported_genders": ["female", "male", "non-binary"],
        "supported_age_groups": ["18-25", "26-35", "36-45", "46-55", "55+"],
        "voice_style_note": "For non-binary users: specify 'voice_style' as 'male' or 'female' since blog avatars only support binary options",
        "performance": "All image and video generation uses concurrent processing for maximum speed"
    }


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
    visual_style: str = Form(None),
    voice_style: str = Form(None)  # For non-binary users to specify voice preference
):
    """Generate a quirky daily journal video from user's input video using ASYNC processing."""
    
    # Map frontend style to internal style string
    internal_style = STYLE_MAP.get(visual_style, visual_style)
    
    # Generate unique job ID and start logging
    job_id = logger.generate_job_id()
    logger.log_job_start(job_id, mood)
    logger.log_step(job_id, "USER_INPUT", f"gender={gender}, age_group={age_group}, visual_style={internal_style}, mode=ASYNC")
    
    start_time = time.time()
    
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
        
        # Step 2: Analyze transcript with GCP NLP
        logger.log_step(job_id, "ANALYSIS_START", "Analyzing transcript with GCP NLP...")
        sentiment_data = analyze_transcript(transcript)
        logger.log_analysis(job_id, sentiment_data)
        
        # Step 3: Extract key phrases for video generation (up to 5 phrases)
        logger.log_step(job_id, "KEY_PHRASES_START", "Extracting key phrases...")
        key_phrases = extract_key_phrases(transcript, sentiment_data, num_phrases=5, gender=gender, age_group=age_group, visual_style=internal_style)
        logger.log_key_phrases(job_id, key_phrases)
        
        # Step 4: Create a beautiful script for audio narration
        logger.log_step(job_id, "SCRIPT_CREATION", "Creating audio script...")
        script = beautify_transcript(transcript, mood, sentiment_data, gender=gender, age_group=age_group, visual_style=internal_style)
        
        # Step 5: Generate audio narration
        logger.log_step(job_id, "AUDIO_START", "Generating audio narration...")
        # For non-binary users, use voice_style preference for audio generation
        audio_gender = gender
        if gender and gender.lower() in ["non-binary", "nonbinary", "non_binary"] and voice_style:
            audio_gender = voice_style
        audio_path = generate_voice(script, job_id, gender=audio_gender)
        logger.log_audio_generation(job_id, script, audio_path)

        # Step 6: Generate videos using ASYNC processing for all styles
        stylized = ["Studio Ghibli", "Pixar", "Anime", "Watercolor", "Cyberpunk"]
        if internal_style in stylized:
            # Always use ASYNC concurrent processing for stylized content
            logger.log_step(job_id, "ASYNC_STYLIZED_START", f"Starting async stylized pipeline for {internal_style}")
            video_paths = await _generate_stylized_videos_async(key_phrases, job_id)
        elif visual_style == "blog-female":
            # Use blog avatar video with any_female_primary
            video_path = generate_blog_avatar_video(script, "any_female_primary", 0, job_id)
            video_paths = [video_path]
        elif visual_style == "blog-male":
            # Use blog avatar video with any_male_primary
            video_path = generate_blog_avatar_video(script, "any_male_primary", 0, job_id)
            video_paths = [video_path]
        elif visual_style == "blog-nonbinary" or visual_style == "blog-non-binary":
            # Use blog avatar video with neutral avatar (fallback to any_female_primary for now)
            video_path = generate_blog_avatar_video(script, "any_female_primary", 0, job_id)
            video_paths = [video_path]
        else:
            # Default/Realistic: always use async pipeline
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
        
        total_time = time.time() - start_time
        
        # Log job completion
        logger.log_job_complete(job_id, final_video_path, len(video_paths), len(key_phrases))
        logger.log_step(job_id, "PIPELINE_COMPLETE", f"Total processing time: {total_time:.2f}s")

        return {
            "job_id": job_id,
            "video": final_video_path,
            "transcript": transcript,
            "key_phrases": key_phrases,
            "generated_videos": len(video_paths),
            "processing_time": round(total_time, 2),
            "success_rate": f"{(len(video_paths)/len(key_phrases))*100:.1f}%" if key_phrases else "100%",
            "job_folder": logger.get_job_folder(job_id),
            "gender": gender,
            "age_group": age_group,
            "visual_style": internal_style,
            "mode": "ASYNC"
        }
        
    except Exception as e:
        logger.log_job_error(job_id, str(e), "PIPELINE")
        return {
            "error": f"Job failed: {str(e)}",
            "job_id": job_id
        }


@app.post("/generate-from-text")
async def generate_from_text(
    text: str = Form(...),
    mood: str = Form("Reflective"),
    gender: str = Form("female"),
    age_group: str = Form("26-35"),
    visual_style: str = Form("Studio Ghibli"),
    voice_style: str = Form(None)  # For non-binary users to specify voice preference
):
    """Generate a video directly from text using ASYNC processing (no video upload required)."""
    
    # Map frontend style to internal style string
    internal_style = STYLE_MAP.get(visual_style, visual_style)
    
    # Generate unique job ID and start logging
    job_id = logger.generate_job_id()
    logger.log_job_start(job_id, mood)
    logger.log_step(job_id, "TEXT_INPUT", f"Processing text input: {text[:100]}... (gender={gender}, age_group={age_group}, visual_style={internal_style}, mode=ASYNC)")
    
    start_time = time.time()
    
    try:
        # Step 1: Analyze text with GCP NLP (skip transcription)
        logger.log_step(job_id, "ANALYSIS_START", "Analyzing text with GCP NLP...")
        sentiment_data = analyze_transcript(text)
        logger.log_analysis(job_id, sentiment_data)
        
        # Step 2: Extract key phrases for video generation (up to 5 phrases)
        logger.log_step(job_id, "KEY_PHRASES_START", "Extracting key phrases...")
        key_phrases = extract_key_phrases(text, sentiment_data, num_phrases=5, gender=gender, age_group=age_group, visual_style=internal_style)
        logger.log_key_phrases(job_id, key_phrases)
        
        # Step 3: Generate videos using ASYNC processing for all styles
        stylized = ["Studio Ghibli", "Pixar", "Anime", "Watercolor", "Cyberpunk"]
        if internal_style in stylized:
            # Always use ASYNC concurrent processing for stylized content
            logger.log_step(job_id, "ASYNC_STYLIZED_START", f"Starting async stylized pipeline for {internal_style}")
            video_paths = await _generate_stylized_videos_async(key_phrases, job_id)
        elif visual_style == "blog-female":
            # Create script for blog avatar
            script = beautify_transcript(text, mood, sentiment_data, gender=gender, age_group=age_group, visual_style=internal_style)
            video_path = generate_blog_avatar_video(script, "any_female_primary", 0, job_id)
            video_paths = [video_path]
        elif visual_style == "blog-male":
            # Create script for blog avatar
            script = beautify_transcript(text, mood, sentiment_data, gender=gender, age_group=age_group, visual_style=internal_style)
            video_path = generate_blog_avatar_video(script, "any_male_primary", 0, job_id)
            video_paths = [video_path]
        elif visual_style == "blog-nonbinary" or visual_style == "blog-non-binary":
            # Create script for blog avatar
            script = beautify_transcript(text, mood, sentiment_data, gender=gender, age_group=age_group, visual_style=internal_style)
            video_path = generate_blog_avatar_video(script, "any_female_primary", 0, job_id)
            video_paths = [video_path]
        else:
            # Default/Realistic: always use async pipeline
            logger.log_video_generation_start(job_id, len(key_phrases))
            video_paths = await async_generate_videos_from_phrases(key_phrases, job_id)

        if not video_paths:
            error_msg = "Failed to generate any videos"
            logger.log_job_error(job_id, error_msg, "VIDEO_GENERATION")
            return {"error": error_msg, "job_id": job_id}
        
        # Step 4: Stitch videos together
        logger.log_step(job_id, "STITCHING_START", f"Stitching {len(video_paths)} videos together...")
        stitched_video_path = logger.get_job_file_path(job_id, "stitched_video.mp4")
        final_stitched_path = stitch_videos(video_paths, stitched_video_path)
        
        # Step 5: Get video duration for text generation
        logger.log_step(job_id, "DURATION_DETECTION", "Detecting video duration...")
        video_duration = get_video_duration(final_stitched_path)
        if not video_duration:
            # Fallback: estimate duration based on number of videos (5 seconds each)
            video_duration = len(video_paths) * 5.0
            logger.log_step(job_id, "DURATION_FALLBACK", f"Using estimated duration: {video_duration:.2f}s")
        
        # Step 6: Generate matching text
        logger.log_step(job_id, "TEXT_GENERATION", "Generating text with OpenAI GPT-4o...")
        from test_pipeline import generate_text_for_video_length
        generated_text = generate_text_for_video_length(video_duration, text, job_id, key_phrases)
        if not generated_text:
            # Fallback to original text if generation fails
            generated_text = text
            logger.log_step(job_id, "TEXT_GENERATION_FALLBACK", "Using original text as fallback")
        
        # Step 7: Generate audio narration
        logger.log_step(job_id, "AUDIO_START", "Generating audio with ElevenLabs...")
        # For non-binary users, use voice_style preference for audio generation
        audio_gender = gender
        if gender.lower() in ["non-binary", "nonbinary", "non_binary"] and voice_style:
            audio_gender = voice_style
        audio_path = generate_voice(generated_text, job_id, gender=audio_gender)
        logger.log_audio_generation(job_id, generated_text, audio_path)
        
        # Step 8: Create final video with audio
        logger.log_step(job_id, "FINAL_VIDEO_START", "Creating final narrated video...")
        final_video_path = logger.get_job_file_path(job_id, "final_narrated_video.mp4")
        from .video_assembler import add_audio_to_video
        combined_video_path = add_audio_to_video(final_stitched_path, audio_path, final_video_path)
        
        total_time = time.time() - start_time
        
        # Log job completion
        logger.log_job_complete(job_id, combined_video_path, len(video_paths), len(key_phrases))
        logger.log_step(job_id, "PIPELINE_COMPLETE", f"Total processing time: {total_time:.2f}s")

        return {
            "job_id": job_id,
            "video": combined_video_path,
            "original_text": text,
            "generated_text": generated_text,
            "key_phrases": key_phrases,
            "generated_videos": len(video_paths),
            "video_duration": video_duration,
            "processing_time": round(total_time, 2),
            "success_rate": f"{(len(video_paths)/len(key_phrases))*100:.1f}%" if key_phrases else "100%",
            "job_folder": logger.get_job_folder(job_id),
            "gender": gender,
            "age_group": age_group,
            "visual_style": internal_style,
            "mode": "ASYNC"
        }
        
    except Exception as e:
        logger.log_job_error(job_id, str(e), "TEXT_PIPELINE")
        return {
            "error": f"Text pipeline failed: {str(e)}",
            "job_id": job_id
        }


@app.post("/text-to-blog")
async def text_to_blog(
    text: str = Form(...),
    name: str = Form(...),
    gender: str = Form("female"),
    age_group: str = Form("26-35"),
    mood: str = Form("Reflective"),
    voice_style: str = Form(None)  # For non-binary users to specify voice preference
):
    """Generate a 25-second talking avatar video from text input using blog avatars."""
    
    # Generate unique job ID and start logging
    job_id = logger.generate_job_id()
    logger.log_job_start(job_id, mood)
    logger.log_step(job_id, "TEXT_TO_BLOG_START", f"Processing text-to-blog request for {name}: {text[:100]}... (gender={gender}, age_group={age_group}, mood={mood})")
    
    start_time = time.time()
    
    try:
        # Step 1: Generate a coherent 25-second dialog from the input text (third-person)
        logger.log_step(job_id, "DIALOG_GENERATION", f"Generating 25-second coherent third-person dialog about {name}...")
        from test_pipeline import generate_text_for_video_length
        dialog = generate_text_for_video_length(25.0, text, job_id, third_person=True, person_name=name)
        
        if not dialog:
            # Fallback to original text if generation fails
            dialog = text
            logger.log_step(job_id, "DIALOG_FALLBACK", "Using original text as fallback for dialog")
        
        logger.log_step(job_id, "DIALOG_COMPLETE", f"Generated third-person dialog about {name}: {dialog[:100]}...")
        
        # Step 2: Determine avatar ID based on gender
        if gender.lower() == "female":
            avatar_id = "any_female_primary"
        elif gender.lower() == "male":
            avatar_id = "any_male_primary"
        elif gender.lower() in ["non-binary", "nonbinary", "non_binary"]:
            # For non-binary users, use voice_style preference since blog avatars only support male/female
            if voice_style and voice_style.lower() == "male":
                avatar_id = "any_male_primary"
            else:
                # Default to female voice/avatar if no preference specified
                avatar_id = "any_female_primary"
        else:
            # Default fallback
            avatar_id = "any_female_primary"
        logger.log_step(job_id, "AVATAR_SELECTION", f"Selected avatar: {avatar_id} for gender: {gender}, voice_style: {voice_style}")
        
        # Step 3: Generate talking avatar video (handles both video and audio automatically)
        logger.log_step(job_id, "AVATAR_VIDEO_START", "Generating talking avatar video with audio...")
        video_path = generate_blog_avatar_video(dialog, avatar_id, 0, job_id)
        
        if not video_path or not os.path.exists(video_path):
            error_msg = "Failed to generate blog avatar video"
            logger.log_job_error(job_id, error_msg, "AVATAR_VIDEO_GENERATION")
            return {"error": error_msg, "job_id": job_id}
        
        total_time = time.time() - start_time
        
        # Log job completion
        logger.log_job_complete(job_id, video_path, 1, 1)
        logger.log_step(job_id, "TEXT_TO_BLOG_COMPLETE", f"Total processing time: {total_time:.2f}s")

        return {
            "job_id": job_id,
            "video": video_path,
            "original_text": text,
            "generated_dialog": dialog,
            "person_name": name,
            "avatar_id": avatar_id,
            "dialog_duration": 25.0,
            "processing_time": round(total_time, 2),
            "job_folder": logger.get_job_folder(job_id),
            "gender": gender,
            "age_group": age_group,
            "mood": mood,
            "note": f"Video includes automatically generated audio of the avatar speaking about {name} in third-person"
        }
        
    except Exception as e:
        logger.log_job_error(job_id, str(e), "TEXT_TO_BLOG_PIPELINE")
        return {
            "error": f"Text-to-blog pipeline failed: {str(e)}",
            "job_id": job_id
        }


async def _generate_stylized_videos_async(key_phrases: list[str], job_id: str) -> list[str]:
    """Helper function to generate stylized videos using async concurrent processing."""
    # Create all image generation tasks
    image_tasks = []
    image_paths = []
    for i, phrase in enumerate(key_phrases):
        image_path = logger.get_job_file_path(job_id, f"openai_image_{i}.png")
        image_paths.append(image_path)
        task = async_generate_image_with_openai(phrase, image_path)
        image_tasks.append(task)
    
    # Generate all images concurrently
    logger.log_step(job_id, "ASYNC_IMAGE_GENERATION", f"Generating {len(image_tasks)} images concurrently")
    image_results = await asyncio.gather(*image_tasks, return_exceptions=True)
    
    # Check image generation results
    successful_images = []
    for i, result in enumerate(image_results):
        if isinstance(result, Exception):
            logger.log_step(job_id, "IMAGE_ERROR", f"Image {i+1} failed: {result}")
        else:
            logger.log_step(job_id, "IMAGE_SUCCESS", f"Image {i+1} generated: {result}")
            successful_images.append((i, result, key_phrases[i]))
    
    if not successful_images:
        raise Exception("Failed to generate any images")
    
    # Upload all images (could be made async too, but keeping simple for now)
    for i, image_path, phrase in successful_images:
        try:
            upload_url = upload_image(image_path)
            logger.log_step(job_id, "IMAGE_UPLOAD", f"Image {i+1} uploaded: {upload_url}")
        except Exception as e:
            logger.log_step(job_id, "UPLOAD_ERROR", f"Upload failed for image {i+1}: {e}")
            # Remove from successful images if upload fails
            successful_images = [(idx, path, phr) for idx, path, phr in successful_images if idx != i]
    
    if not successful_images:
        raise Exception("Failed to upload any images")
    
    # Create all video generation tasks
    video_tasks = []
    for i, image_path, phrase in successful_images:
        task = async_generate_video_from_image(image_path, phrase, i, job_id)
        video_tasks.append(task)
    
    # Generate all videos concurrently
    logger.log_step(job_id, "ASYNC_VIDEO_GENERATION", f"Generating {len(video_tasks)} videos concurrently")
    video_results = await asyncio.gather(*video_tasks, return_exceptions=True)
    
    # Check video generation results
    video_paths = []
    for i, result in enumerate(video_results):
        if isinstance(result, Exception):
            logger.log_step(job_id, "VIDEO_ERROR", f"Video {i+1} failed: {result}")
        else:
            logger.log_step(job_id, "VIDEO_SUCCESS", f"Video {i+1} generated: {result}")
            video_paths.append(result)
    
    logger.log_step(job_id, "ASYNC_STYLIZED_COMPLETE", f"Generated {len(video_paths)}/{len(key_phrases)} videos using async processing")
    return video_paths
