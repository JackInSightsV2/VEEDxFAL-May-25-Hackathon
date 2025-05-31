"""Video generation module using FAL API."""

import os
import fal_client
import requests
from .logger import logger
import asyncio
import httpx
import base64
from .azure_uploader import upload_image

# Ensure FAL_KEY is set for fal_client library
def ensure_fal_key():
    """Ensure FAL_KEY is properly set for the fal_client library."""
    fal_key = os.getenv("FAL_KEY")
    fal_api_key = os.getenv("FAL_API_KEY")
    
    if not fal_key and fal_api_key:
        os.environ["FAL_KEY"] = fal_api_key
        print(f"🔧 Mapped FAL_API_KEY to FAL_KEY")
        return True
    elif fal_key:
        return True
    else:
        print("❌ No FAL API key found. Please set either FAL_KEY or FAL_API_KEY in your .env file")
        return False

# Call this when the module is imported
ensure_fal_key()

def generate_video_from_text(prompt: str, video_id: int = 0, job_id: str = None) -> str:
    """Generate a video based on the text prompt and return the video path."""
    
    # Double-check FAL key before making API call
    if not ensure_fal_key():
        raise Exception("FAL API key not configured. Please set FAL_KEY or FAL_API_KEY in your .env file")
    
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                message = f"Video {video_id + 1} generation: {log['message']}"
                print(message)
                if job_id:
                    logger.log_step(job_id, "VIDEO_PROGRESS", message)
    
    try:
        if job_id:
            logger.log_step(job_id, "VIDEO_CLIP_START", f"Starting generation of video clip {video_id + 1}", {"prompt": prompt})
        
        # Use FAL client with the correct v2.1/master endpoint
        result = fal_client.subscribe(
            "fal-ai/kling-video/v2.1/master/text-to-video",
            arguments={
                "prompt": prompt,
                "duration": "5",  # 5 second videos
                "aspect_ratio": "9:16",  # TikTok/Instagram format
                "negative_prompt": "blur, distort, and low quality"
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
        
        # Extract video URL from result
        video_url = result.get("video", {}).get("url")
        
        if not video_url:
            raise Exception("No video URL returned from FAL API")
        
        # Download the video to job folder
        if job_id:
            video_path = logger.get_job_file_path(job_id, f"video_clip_{video_id}.mp4")
        else:
            video_path = f"video_clip_{video_id}.mp4"
        
        video_response = requests.get(video_url)
        video_response.raise_for_status()
        
        with open(video_path, "wb") as f:
            f.write(video_response.content)
        
        success_msg = f"✅ Video {video_id + 1} saved as: {video_path}"
        print(success_msg)
        
        if job_id:
            logger.log_video_clip_generated(job_id, video_id + 1, 0, prompt, video_path)  # total_clips will be updated by caller
        
        return video_path
        
    except Exception as e:
        error_msg = f"❌ Error generating video {video_id + 1}: {e}"
        print(error_msg)
        
        if job_id:
            logger.log_video_clip_error(job_id, video_id + 1, 0, prompt, str(e))  # total_clips will be updated by caller
        
        raise e


def generate_videos_from_phrases(key_phrases: list[str], job_id: str = None) -> list[str]:
    """Generate multiple videos from key phrases."""
    video_paths = []
    total_phrases = len(key_phrases)
    
    print(f"🎬 Starting generation of {total_phrases} videos...")
    if job_id:
        logger.log_step(job_id, "BATCH_VIDEO_START", f"Starting batch generation of {total_phrases} videos")
    
    for i, phrase in enumerate(key_phrases):
        print(f"\n📹 Generating video {i+1}/{total_phrases}")
        print(f"Prompt: {phrase[:100]}{'...' if len(phrase) > 100 else ''}")
        
        try:
            video_path = generate_video_from_text(phrase, i, job_id)
            video_paths.append(video_path)
            
            success_msg = f"✅ Video {i+1} completed!"
            print(success_msg)
            
            if job_id:
                # Update the log entry with correct total count
                logger.log_step(job_id, "VIDEO_CLIP_SUCCESS", f"Successfully generated video {i+1}/{total_phrases}")
                
        except Exception as e:
            error_msg = f"❌ Error generating video {i+1}: {e}"
            print(error_msg)
            # Continue with other videos even if one fails
            continue
    
    completion_msg = f"🎉 Generated {len(video_paths)} out of {total_phrases} videos successfully!"
    print(completion_msg)
    
    if job_id:
        logger.log_step(job_id, "BATCH_VIDEO_COMPLETE", completion_msg, {
            "successful_videos": len(video_paths),
            "total_requested": total_phrases,
            "success_rate": f"{(len(video_paths)/total_phrases)*100:.1f}%" if total_phrases > 0 else "0%"
        })
    
    return video_paths


# Keep the old function name for backwards compatibility, but mark as deprecated
def generate_image(prompt: str) -> str:
    """Deprecated: Use generate_video_from_text instead."""
    print("Warning: generate_image is deprecated. Use generate_video_from_text instead.")
    return generate_video_from_text(prompt, 0)

async def async_generate_video_from_text(prompt: str, video_id: int = 0, job_id: str = None) -> str:
    """Async version: Generate a video based on the text prompt and return the video path."""
    import functools
    # Double-check FAL key before making API call
    if not ensure_fal_key():
        raise Exception("FAL API key not configured. Please set FAL_KEY or FAL_API_KEY in your .env file")

    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                message = f"Video {video_id + 1} generation: {log['message']}"
                print(message)
                if job_id:
                    logger.log_step(job_id, "VIDEO_PROGRESS", message)

    # fal_client.subscribe is blocking, so run it in a thread
    result = await asyncio.to_thread(
        functools.partial(
            fal_client.subscribe,
            "fal-ai/kling-video/v2.1/master/text-to-video",
            arguments={
                "prompt": prompt,
                "duration": "5",
                "aspect_ratio": "9:16",
                "negative_prompt": "blur, distort, and low quality"
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )
    )

    video_url = result.get("video", {}).get("url")
    if not video_url:
        raise Exception("No video URL returned from FAL API")

    if job_id:
        video_path = logger.get_job_file_path(job_id, f"video_clip_{video_id}.mp4")
    else:
        video_path = f"video_clip_{video_id}.mp4"

    async with httpx.AsyncClient() as client:
        video_response = await client.get(video_url)
        video_response.raise_for_status()
        with open(video_path, "wb") as f:
            f.write(video_response.content)

    success_msg = f"✅ Video {video_id + 1} saved as: {video_path}"
    print(success_msg)
    if job_id:
        logger.log_video_clip_generated(job_id, video_id + 1, 0, prompt, video_path)
    return video_path

async def async_generate_videos_from_phrases(key_phrases: list[str], job_id: str = None) -> list[str]:
    """Async version: Generate multiple videos from key phrases concurrently (up to 5)."""
    total_phrases = len(key_phrases)
    print(f"🎬 Starting async generation of {total_phrases} videos...")
    if job_id:
        logger.log_step(job_id, "BATCH_VIDEO_START", f"Starting async batch generation of {total_phrases} videos")

    # Launch all video generations concurrently
    tasks = [
        async_generate_video_from_text(phrase, i, job_id)
        for i, phrase in enumerate(key_phrases)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    video_paths = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"❌ Error generating video {i+1}: {result}")
            continue
        video_paths.append(result)
        print(f"✅ Video {i+1} completed!")
        if job_id:
            logger.log_step(job_id, "VIDEO_CLIP_SUCCESS", f"Successfully generated video {i+1}/{total_phrases}")

    completion_msg = f"🎉 Generated {len(video_paths)} out of {total_phrases} videos successfully!"
    print(completion_msg)
    if job_id:
        logger.log_step(job_id, "BATCH_VIDEO_COMPLETE", completion_msg, {
            "successful_videos": len(video_paths),
            "total_requested": total_phrases,
            "success_rate": f"{(len(video_paths)/total_phrases)*100:.1f}%" if total_phrases > 0 else "0%"
        })
    return video_paths

def generate_video_from_image(image_path: str, prompt: str, video_id: int = 0, job_id: str = None) -> str:
    """Generate a video from an image using FAL's veo2 image-to-video endpoint."""
    if not ensure_fal_key():
        raise Exception("FAL API key not configured. Please set FAL_KEY or FAL_API_KEY in your .env file")

    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                message = f"Image-to-Video {video_id + 1} generation: {log['message']}"
                print(message)
                if job_id:
                    logger.log_step(job_id, "VIDEO_PROGRESS", message)

    try:
        if job_id:
            logger.log_step(job_id, "VIDEO_CLIP_START", f"Starting image-to-video clip {video_id + 1}", {"prompt": prompt, "image_path": image_path})

        # Upload image to Azure and get the URL
        image_url = upload_image(image_path, job_id=job_id)

        result = fal_client.subscribe(
            "fal-ai/veo2/image-to-video",
            arguments={
                "prompt": prompt,
                "image_url": image_url
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )

        video_url = result.get("video", {}).get("url")
        if not video_url:
            raise Exception("No video URL returned from FAL API (veo2 image-to-video)")

        if job_id:
            video_path = logger.get_job_file_path(job_id, f"video_clip_{video_id}.mp4")
        else:
            video_path = f"video_clip_{video_id}.mp4"

        video_response = requests.get(video_url)
        video_response.raise_for_status()
        with open(video_path, "wb") as f:
            f.write(video_response.content)

        print(f"✅ Image-to-Video {video_id + 1} saved as: {video_path}")
        if job_id:
            logger.log_video_clip_generated(job_id, video_id + 1, 0, prompt, video_path)
        return video_path
    except Exception as e:
        print(f"❌ Error generating image-to-video {video_id + 1}: {e}")
        if job_id:
            logger.log_video_clip_error(job_id, video_id + 1, 0, prompt, str(e))
        raise e

async def async_generate_video_from_image(image_path: str, prompt: str, video_id: int = 0, job_id: str = None) -> str:
    """Async version: Generate a video from an image using FAL's veo2 image-to-video endpoint."""
    import functools
    if not ensure_fal_key():
        raise Exception("FAL API key not configured. Please set FAL_KEY or FAL_API_KEY in your .env file")

    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                message = f"Image-to-Video {video_id + 1} generation: {log['message']}"
                print(message)
                if job_id:
                    logger.log_step(job_id, "VIDEO_PROGRESS", message)

    try:
        if job_id:
            logger.log_step(job_id, "VIDEO_CLIP_START", f"Starting async image-to-video clip {video_id + 1}", {"prompt": prompt, "image_path": image_path})

        # Upload image to Azure and get the URL (run in thread since it might be blocking)
        image_url = await asyncio.to_thread(upload_image, image_path, 1, job_id)

        # Run the FAL API call in a thread since it's blocking
        result = await asyncio.to_thread(
            functools.partial(
                fal_client.subscribe,
                "fal-ai/veo2/image-to-video",
                arguments={
                    "prompt": prompt,
                    "image_url": image_url
                },
                with_logs=True,
                on_queue_update=on_queue_update,
            )
        )

        video_url = result.get("video", {}).get("url")
        if not video_url:
            raise Exception("No video URL returned from FAL API (veo2 image-to-video)")

        if job_id:
            video_path = logger.get_job_file_path(job_id, f"video_clip_{video_id}.mp4")
        else:
            video_path = f"video_clip_{video_id}.mp4"

        # Download video asynchronously
        async with httpx.AsyncClient() as client:
            video_response = await client.get(video_url)
            video_response.raise_for_status()
            with open(video_path, "wb") as f:
                f.write(video_response.content)

        print(f"✅ Async Image-to-Video {video_id + 1} saved as: {video_path}")
        if job_id:
            logger.log_video_clip_generated(job_id, video_id + 1, 0, prompt, video_path)
        return video_path
    except Exception as e:
        print(f"❌ Error generating async image-to-video {video_id + 1}: {e}")
        if job_id:
            logger.log_video_clip_error(job_id, video_id + 1, 0, prompt, str(e))
        raise e

def generate_blog_avatar_video(text: str, avatar_id: str, video_id: int = 0, job_id: str = None) -> str:
    """Generate a blog avatar video using veed/avatars/text-to-video."""
    if not ensure_fal_key():
        raise Exception("FAL API key not configured. Please set FAL_KEY or FAL_API_KEY in your .env file")

    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                message = f"Blog Avatar Video {video_id + 1} generation: {log['message']}"
                print(message)
                if job_id:
                    logger.log_step(job_id, "VIDEO_PROGRESS", message)

    try:
        if job_id:
            logger.log_step(job_id, "VIDEO_CLIP_START", f"Starting blog avatar video {video_id + 1}", {"avatar_id": avatar_id, "text": text[:50]})

        result = fal_client.subscribe(
            "veed/avatars/text-to-video",
            arguments={
                "avatar_id": avatar_id,
                "text": text
            },
            with_logs=True,
            on_queue_update=on_queue_update,
        )

        video_url = result.get("video", {}).get("url")
        if not video_url:
            raise Exception("No video URL returned from FAL API (blog avatar video)")

        if job_id:
            video_path = logger.get_job_file_path(job_id, f"blog_avatar_{video_id}.mp4")
        else:
            video_path = f"blog_avatar_{video_id}.mp4"

        video_response = requests.get(video_url)
        video_response.raise_for_status()
        with open(video_path, "wb") as f:
            f.write(video_response.content)

        print(f"✅ Blog Avatar Video {video_id + 1} saved as: {video_path}")
        if job_id:
            logger.log_video_clip_generated(job_id, video_id + 1, 0, text, video_path)
        return video_path
    except Exception as e:
        print(f"❌ Error generating blog avatar video {video_id + 1}: {e}")
        if job_id:
            logger.log_video_clip_error(job_id, video_id + 1, 0, text, str(e))
        raise e
