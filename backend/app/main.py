from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import time
import os

from .azure_uploader import list_mp4_videos
from .logger import logger
from .pipeline.context import PipelineContext
from .pipeline.orchestrator import PipelineOrchestrator

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STYLE_MAP = {
    "ghibli": "Studio Ghibli",
    "pixar": "Pixar",
    "anime": "Anime",
    "watercolor": "Watercolor",
    "cyberpunk": "Cyberpunk",
    "blog-female": "Blog (Female)",
    "blog-male": "Blog (Male)",
    "blog-nonbinary": "Blog (Nonbinary)",
    "blog-non-binary": "Blog (Nonbinary)",
    "realistic": "Realistic"
}

pipeline_orchestrator = PipelineOrchestrator()


def _round_time(seconds: float) -> float:
    return round(seconds, 2)


def _finalize_job(ctx: PipelineContext, total_time: float) -> float:
    final_asset = ctx.final_video_path or (ctx.video_paths[0] if ctx.video_paths else None)
    logger.log_job_complete(
        ctx.job_id,
        final_asset,
        len(ctx.video_paths),
        len(ctx.key_phrases),
    )
    rounded = _round_time(total_time)
    logger.log_step(ctx.job_id, "PIPELINE_COMPLETE", f"Total processing time: {rounded:.2f}s")
    return rounded


def _build_stylized_response(ctx: PipelineContext, rounded_time: float, original_text: str | None) -> dict:
    display_style = ctx.metadata.get("display_style", ctx.visual_style)
    return {
        "job_id": ctx.job_id,
        "video": ctx.final_video_path,
        "original_text": original_text,
        "generated_text": ctx.generated_text,
        "key_phrases": ctx.key_phrases,
        "generated_videos": ctx.metadata.get("generated_videos", len(ctx.video_paths)),
        "video_duration": ctx.metadata.get("video_duration"),
        "processing_time": rounded_time,
        "success_rate": ctx.metadata.get("success_rate"),
        "job_folder": logger.get_job_folder(ctx.job_id),
        "gender": ctx.gender,
        "age_group": ctx.age_group,
        "visual_style": display_style,
        "mode": ctx.metadata.get("mode", "ASYNC_STYLIZED"),
        "azure_urls": ctx.azure_urls,
    }


def _build_blog_response(ctx: PipelineContext, rounded_time: float, original_text: str | None) -> dict:
    display_style = ctx.metadata.get("display_style", ctx.visual_style)
    avatar_gender = ctx.metadata.get("avatar_gender")
    story_about = ctx.metadata.get("story_about")
    note = (
        f"{avatar_gender.capitalize()} avatar telling a story about a {story_about} (you) - "
        "video includes built-in lip-synced audio from VEED model"
        if avatar_gender and story_about
        else "Video includes built-in lip-synced audio from VEED model"
    )
    response = {
        "job_id": ctx.job_id,
        "video": ctx.final_video_path,
        "original_text": original_text,
        "generated_story": ctx.generated_text,
        "user_gender": ctx.gender,
        "avatar_gender": avatar_gender,
        "story_about": story_about,
        "processing_time": rounded_time,
        "job_folder": logger.get_job_folder(ctx.job_id),
        "visual_style": display_style,
        "mode": ctx.metadata.get("mode", "BLOG_AVATAR"),
        "azure_urls": ctx.azure_urls,
        "note": note,
    }
    if ctx.metadata.get("voice_style"):
        response["voice_style"] = ctx.metadata["voice_style"]
    if ctx.metadata.get("avatar_id"):
        response["avatar_used"] = ctx.metadata["avatar_id"]
    return response


def _build_default_video_response(ctx: PipelineContext, rounded_time: float) -> dict:
    display_style = ctx.metadata.get("display_style", ctx.visual_style)
    return {
        "job_id": ctx.job_id,
        "video": ctx.final_video_path,
        "transcript": ctx.transcript,
        "generated_text": ctx.generated_text or ctx.script_text,
        "key_phrases": ctx.key_phrases,
        "generated_videos": len(ctx.video_paths),
        "video_duration": ctx.metadata.get("video_duration"),
        "processing_time": rounded_time,
        "success_rate": ctx.metadata.get(
            "success_rate",
            f"{(len(ctx.video_paths) / max(len(ctx.key_phrases), 1)) * 100:.1f}%" if ctx.key_phrases else "100%",
        ),
        "job_folder": logger.get_job_folder(ctx.job_id),
        "gender": ctx.gender,
        "age_group": ctx.age_group,
        "visual_style": display_style,
        "mode": ctx.metadata.get("mode", "ASYNC"),
        "azure_urls": ctx.azure_urls,
    }


def _build_default_text_response(ctx: PipelineContext, rounded_time: float, original_text: str | None) -> dict:
    display_style = ctx.metadata.get("display_style", ctx.visual_style)
    return {
        "job_id": ctx.job_id,
        "video": ctx.final_video_path,
        "original_text": original_text,
        "generated_text": ctx.generated_text,
        "key_phrases": ctx.key_phrases,
        "generated_videos": len(ctx.video_paths),
        "video_duration": ctx.metadata.get("video_duration"),
        "processing_time": rounded_time,
        "success_rate": ctx.metadata.get(
            "success_rate",
            f"{(len(ctx.video_paths) / max(len(ctx.key_phrases), 1)) * 100:.1f}%" if ctx.key_phrases else "100%",
        ),
        "job_folder": logger.get_job_folder(ctx.job_id),
        "gender": ctx.gender,
        "age_group": ctx.age_group,
        "visual_style": display_style,
        "mode": ctx.metadata.get("mode", "ASYNC"),
        "azure_urls": ctx.azure_urls,
    }


def _build_video_generate_response(ctx: PipelineContext, rounded_time: float) -> dict:
    mode = ctx.metadata.get("mode")
    if mode == "ASYNC_STYLIZED":
        return _build_stylized_response(ctx, rounded_time, ctx.transcript)
    if mode == "BLOG_AVATAR":
        return _build_blog_response(ctx, rounded_time, ctx.transcript)
    return _build_default_video_response(ctx, rounded_time)


def _build_text_generate_response(ctx: PipelineContext, rounded_time: float) -> dict:
    mode = ctx.metadata.get("mode")
    original_text = ctx.input_text or ctx.transcript
    if mode == "ASYNC_STYLIZED":
        return _build_stylized_response(ctx, rounded_time, original_text)
    if mode == "BLOG_AVATAR":
        return _build_blog_response(ctx, rounded_time, original_text)
    return _build_default_text_response(ctx, rounded_time, original_text)


def _resolve_blog_style_alias(gender: str | None) -> str:
    if not gender:
        return "blog-female"
    lowered = gender.lower()
    if lowered == "male":
        return "blog-male"
    if lowered in {"non-binary", "nonbinary", "non_binary"}:
        return "blog-nonbinary"
    return "blog-female"

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
                "path": "/text-to-blog",
                "method": "POST",
                "description": "Generate a 25-second talking avatar video from text input using blog avatars.",
                "parameters": ["text", "name", "gender", "age_group", "mood", "voice_style"],
                "processing": "ASYNC"
            },
            {
                "path": "/status/{job_id}",
                "method": "GET",
                "description": "Check the status of a video generation job",
                "returns": "Job status, progress, and video URL when complete"
            },
            {
                "path": "/download/{job_id}",
                "method": "GET", 
                "description": "Download the completed video file",
                "returns": "MP4 video file"
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
                "path": "/examples",
                "method": "GET",
                "description": "Get all example videos from Azure Storage"
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
    voice_style: str = Form(None),
):
    """Generate a video from an uploaded clip using the modular pipeline."""

    internal_style = STYLE_MAP.get(visual_style, visual_style)
    job_id = logger.generate_job_id()

    logger.log_job_start(job_id, mood)
    logger.log_step(
        job_id,
        "USER_INPUT",
        f"gender={gender}, age_group={age_group}, visual_style={internal_style}, mode=ASYNC",
    )

    start_time = time.time()

    try:
        input_video_path = logger.get_job_file_path(job_id, "input_video.mp4")
        logger.log_step(job_id, "UPLOAD", f"Processing uploaded video: {video.filename}")
        with open(input_video_path, "wb") as buffer:
            buffer.write(await video.read())

        ctx = PipelineContext(
            job_id=job_id,
            mood=mood,
            request_type="video",
            gender=gender,
            age_group=age_group,
            visual_style=internal_style,
            voice_style=voice_style,
            input_video_path=input_video_path,
        )
        ctx.metadata["style_alias"] = visual_style
        ctx.metadata["display_style"] = internal_style

        result = await pipeline_orchestrator.run(ctx)
        rounded_time = _finalize_job(result.context, time.time() - start_time)
        return _build_video_generate_response(result.context, rounded_time)

    except Exception as exc:
        logger.log_job_error(job_id, str(exc), "PIPELINE")
        return {"error": f"Job failed: {exc}", "job_id": job_id}


@app.post("/generate-from-text")
async def generate_from_text(
    text: str = Form(...),
    mood: str = Form("Reflective"),
    gender: str = Form("female"),
    age_group: str = Form("26-35"),
    visual_style: str = Form("Studio Ghibli"),
    voice_style: str = Form(None),
):
    """Generate a video directly from text using the modular pipeline."""

    internal_style = STYLE_MAP.get(visual_style, visual_style)
    job_id = logger.generate_job_id()

    logger.log_job_start(job_id, mood)
    logger.log_step(
        job_id,
        "TEXT_INPUT",
        f"Processing text input: {text[:100]}... (gender={gender}, age_group={age_group}, visual_style={internal_style}, mode=ASYNC)",
    )

    start_time = time.time()

    try:
        ctx = PipelineContext(
            job_id=job_id,
            mood=mood,
            request_type="text",
            gender=gender,
            age_group=age_group,
            visual_style=internal_style,
            voice_style=voice_style,
            input_text=text,
        )
        ctx.metadata["style_alias"] = visual_style
        ctx.metadata["display_style"] = internal_style

        result = await pipeline_orchestrator.run(ctx)
        rounded_time = _finalize_job(result.context, time.time() - start_time)
        return _build_text_generate_response(result.context, rounded_time)

    except Exception as exc:
        logger.log_job_error(job_id, str(exc), "TEXT_PIPELINE")
        return {"error": f"Text pipeline failed: {exc}", "job_id": job_id}


@app.post("/text-to-blog")
async def text_to_blog(
    text: str = Form(...),
    name: str = Form(...),
    gender: str = Form("female"),
    age_group: str = Form("26-35"),
    mood: str = Form("Reflective"),
    voice_style: str = Form(None),
):
    """Generate a 25-second talking avatar video from text input using blog avatars."""

    job_id = logger.generate_job_id()

    logger.log_job_start(job_id, mood)
    logger.log_step(
        job_id,
        "TEXT_TO_BLOG_START",
        f"Processing text-to-blog request for {name}: {text[:100]}... (gender={gender}, age_group={age_group}, mood={mood})",
    )

    start_time = time.time()

    try:
        blog_style_alias = _resolve_blog_style_alias(gender)
        internal_style = STYLE_MAP.get(blog_style_alias, blog_style_alias)

        ctx = PipelineContext(
            job_id=job_id,
            mood=mood,
            request_type="text",
            gender=gender,
            age_group=age_group,
            visual_style=internal_style,
            voice_style=voice_style,
            input_text=text,
            person_name=name,
        )
        ctx.metadata["style_alias"] = blog_style_alias
        ctx.metadata["display_style"] = internal_style
        ctx.metadata["person_name"] = name

        result = await pipeline_orchestrator.run(ctx)
        rounded_time = _finalize_job(result.context, time.time() - start_time)
        response = _build_blog_response(result.context, rounded_time, text)
        response.update(
            {
                "generated_dialog": result.context.generated_text,
                "person_name": name,
                "dialog_duration": 25.0,
                "mood": mood,
            }
        )
        return response

    except Exception as exc:
        logger.log_job_error(job_id, str(exc), "TEXT_TO_BLOG_PIPELINE")
        return {"error": f"Text-to-blog pipeline failed: {exc}", "job_id": job_id}


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a video generation job."""
    try:
        # Check if job folder exists
        job_folder = logger.get_job_folder(job_id)
        if not os.path.exists(job_folder):
            return {
                "status": "not_found",
                "progress": 0,
                "error": "Job not found"
            }
        
        # Check for completion by looking for final video file
        final_narrated_path = logger.get_job_file_path(job_id, "final_narrated_video.mp4")
        final_video_path = logger.get_job_file_path(job_id, "final_video.mp4")
        blog_avatar_path = logger.get_job_file_path(job_id, "blog_avatar_0.mp4")
        
        video_file = None
        if os.path.exists(final_narrated_path):
            video_file = final_narrated_path
        elif os.path.exists(final_video_path):
            video_file = final_video_path
        elif os.path.exists(blog_avatar_path):
            video_file = blog_avatar_path
        
        if video_file:
            return {
                "status": "completed",
                "progress": 100,
                "video_url": f"/download/{job_id}",
                "video_path": video_file
            }
        
        # Check if job is in progress by looking at log files
        log_file = os.path.join(job_folder, "job.log")
        if os.path.exists(log_file):
            # Read the log to estimate progress
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
                
            # Simple progress estimation based on log content
            progress = 10  # Started
            if "TRANSCRIPTION_START" in log_content or "TEXT_GENERATION" in log_content:
                progress = 20
            if "ANALYSIS_START" in log_content:
                progress = 30
            if "KEY_PHRASES_START" in log_content:
                progress = 40
            if "AUDIO_START" in log_content:
                progress = 50
            if "VIDEO_GENERATION" in log_content or "ASYNC_STYLIZED_START" in log_content:
                progress = 70
            if "STITCHING_START" in log_content:
                progress = 90
            
            # Blog pipeline specific progress
            if "BLOG_FEMALE_PATH" in log_content or "BLOG_MALE_PATH" in log_content or "BLOG_NONBINARY_PATH" in log_content:
                progress = 30
            if "THIRD_PERSON_STORY" in log_content:
                progress = 50
            if "AVATAR_VIDEO_START" in log_content or "Blog Avatar Video" in log_content:
                progress = 70
            if "AZURE_UPLOAD_SUCCESS" in log_content:
                progress = 95
            
            if "ERROR" in log_content:
                return {
                    "status": "failed",
                    "progress": progress,
                    "error": "Job failed during processing"
                }
                
            return {
                "status": "processing",
                "progress": progress,
                "estimated_time_remaining": "1-2 minutes"
            }
        
        # Job folder exists but no log file - probably just started
        return {
            "status": "processing",
            "progress": 5,
            "estimated_time_remaining": "2-3 minutes"
        }
        
    except Exception as e:
        logger.log_step(job_id, "STATUS_CHECK_ERROR", f"Error checking status: {str(e)}")
        return {
            "status": "failed",
            "progress": 0,
            "error": f"Status check failed: {str(e)}"
        }


@app.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download the completed video for a job."""
    try:
        # Check for final video file
        final_narrated_path = logger.get_job_file_path(job_id, "final_narrated_video.mp4")
        final_video_path = logger.get_job_file_path(job_id, "final_video.mp4")
        blog_avatar_path = logger.get_job_file_path(job_id, "blog_avatar_0.mp4")
        
        video_file = None
        if os.path.exists(final_narrated_path):
            video_file = final_narrated_path
        elif os.path.exists(final_video_path):
            video_file = final_video_path
        elif os.path.exists(blog_avatar_path):
            video_file = blog_avatar_path
        
        if not video_file:
            return {"error": "Video not found or not ready"}
        
        from fastapi.responses import FileResponse
        return FileResponse(
            video_file,
            media_type="video/mp4",
            filename=f"journal_video_{job_id}.mp4"
        )
        
    except Exception as e:
        return {"error": f"Download failed: {str(e)}"}


@app.get("/examples")
async def get_examples():
    """Get all example videos from Azure Storage."""
    try:
        videos = list_mp4_videos()
        return {
            "success": True,
            "videos": videos,
            "count": len(videos)
        }
    except Exception as e:
        logger.log_step("SYSTEM", "EXAMPLES_ERROR", f"Error fetching examples: {e}")
        return {
            "success": False,
            "error": str(e),
            "videos": [],
            "count": 0
        }
