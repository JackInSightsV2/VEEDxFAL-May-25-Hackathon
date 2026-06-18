"""Combine multiple video clips and add audio narration using ffmpeg."""

import shutil
import subprocess
import os
from .logger import logger


def get_video_duration(video_path: str) -> float:
    """Get the duration of a video file in seconds (0.0 if it can't be determined)."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ],
        capture_output=True,
        text=True
    )
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        # ffprobe failed / returned empty (bad codec, missing file) — don't crash
        # the caller (add_audio_to_video); fall back to an unknown duration.
        return 0.0


def stitch_videos(video_paths: list[str], output_path: str = "stitched_video.mp4") -> str:
    """Stitch multiple video clips together."""
    if not video_paths:
        raise ValueError("No video paths provided")
    
    if len(video_paths) == 1:
        # If only one video, just copy it (cross-platform; raises on failure)
        shutil.copy2(video_paths[0], output_path)
        return output_path
    
    # Create a temporary file list for ffmpeg in the same directory as output
    output_dir = os.path.dirname(output_path)
    video_list_path = os.path.join(output_dir, "video_list.txt")
    
    with open(video_list_path, "w") as f:
        for video_path in video_paths:
            f.write(f"file '{video_path}'\n")
    
    # Concatenate videos
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", video_list_path,
            "-c", "copy",
            output_path
        ],
        check=True
    )
    
    # Clean up temporary file
    os.remove(video_list_path)
    
    return output_path


def add_audio_to_video(video_path: str, audio_path: str, output_path: str = "final_video.mp4") -> str:
    """Add audio narration to video, adjusting audio length to match video duration."""
    # Get video duration
    video_duration = get_video_duration(video_path)
    
    # Create temporary audio file with adjusted length in the same directory as output
    output_dir = os.path.dirname(output_path)
    temp_audio = os.path.join(output_dir, "temp_adjusted_audio.mp3")
    
    # Adjust audio to match video length (speed up/slow down or loop/cut)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", audio_path,
            "-filter:a", f"atempo=1.0",  # Keep original tempo for now
            "-t", str(video_duration),  # Cut audio to video length
            temp_audio
        ],
        check=True
    )
    
    # Combine video and adjusted audio
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-i", temp_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path
        ],
        check=True
    )
    
    # Clean up temporary audio file
    os.remove(temp_audio)
    
    return output_path


def create_final_video(video_paths: list[str], audio_path: str, job_id: str = None, output_path: str = "final.mp4") -> str:
    """Complete pipeline: stitch videos and add audio narration."""
    
    # Determine output paths based on job_id
    if job_id:
        stitched_video_path = logger.get_job_file_path(job_id, "stitched_video.mp4")
        final_video_path = logger.get_job_file_path(job_id, output_path)
    else:
        stitched_video_path = "stitched_video.mp4"
        final_video_path = output_path
    
    # Step 1: Stitch all video clips together
    stitched_video = stitch_videos(video_paths, stitched_video_path)
    
    # Step 2: Add audio narration that matches the video length
    final_video = add_audio_to_video(stitched_video, audio_path, final_video_path)
    
    # Clean up intermediate files
    if os.path.exists(stitched_video_path):
        os.remove(stitched_video_path)
    
    return final_video


# Keep the old function for backwards compatibility
def create_video(image_path: str, audio_path: str, output_path: str = "final.mp4") -> str:
    """Deprecated: Use create_final_video for multi-video workflow."""
    print("Warning: create_video is deprecated for the new multi-video workflow.")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-i",
            audio_path,
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-shortest",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]
    )
    return output_path
