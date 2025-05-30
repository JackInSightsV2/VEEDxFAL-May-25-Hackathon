"""Logging utility for tracking video generation jobs."""

import os
import uuid
import datetime
import json
from typing import Dict, Any


class JobLogger:
    """Logger for tracking video generation jobs with UUIDs."""
    
    def __init__(self, log_file: str = "logs.txt", jobs_dir: str = "jobs"):
        self.log_file = log_file
        self.jobs_dir = jobs_dir
        self.ensure_log_file_exists()
        self.ensure_jobs_dir_exists()
    
    def ensure_log_file_exists(self):
        """Create log file if it doesn't exist."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                f.write("=== Video Generation Job Logs ===\n")
                f.write(f"Log started: {datetime.datetime.now()}\n\n")
    
    def ensure_jobs_dir_exists(self):
        """Create jobs directory if it doesn't exist."""
        if not os.path.exists(self.jobs_dir):
            os.makedirs(self.jobs_dir)
    
    def generate_job_id(self) -> str:
        """Generate a unique job ID."""
        return str(uuid.uuid4())
    
    def create_job_folder(self, job_id: str) -> str:
        """Create a folder for the job and return the path."""
        job_folder = os.path.join(self.jobs_dir, job_id)
        if not os.path.exists(job_folder):
            os.makedirs(job_folder)
        return job_folder
    
    def get_job_folder(self, job_id: str) -> str:
        """Get the job folder path."""
        return os.path.join(self.jobs_dir, job_id)
    
    def get_job_file_path(self, job_id: str, filename: str) -> str:
        """Get a file path within the job folder."""
        return os.path.join(self.get_job_folder(job_id), filename)
    
    def log_step(self, job_id: str, step: str, message: str, data: Dict[Any, Any] = None):
        """Log a step in the job processing pipeline."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "timestamp": timestamp,
            "job_id": job_id,
            "step": step,
            "message": message,
            "data": data or {}
        }
        
        # Write to log file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] JOB:{job_id} | {step} | {message}\n")
            if data:
                f.write(f"  Data: {json.dumps(data, indent=2)}\n")
            f.write("\n")
        
        # Also print to console
        print(f"🔍 [{step}] {message} (Job: {job_id[:8]}...)")
        if data and any(data.values()):
            print(f"   📊 {data}")
    
    def log_job_start(self, job_id: str, mood: str = "Reflective"):
        """Log the start of a new job and create job folder."""
        job_folder = self.create_job_folder(job_id)
        self.log_step(
            job_id, 
            "JOB_START", 
            f"New video generation job started with mood: {mood}. Job folder: {job_folder}",
            {"mood": mood, "job_folder": job_folder}
        )
    
    def log_transcription(self, job_id: str, transcript: str):
        """Log transcription completion."""
        self.log_step(
            job_id,
            "TRANSCRIPTION",
            f"Video transcribed successfully ({len(transcript)} characters)",
            {"transcript_length": len(transcript), "transcript_preview": transcript[:100] + "..." if len(transcript) > 100 else transcript}
        )
    
    def log_analysis(self, job_id: str, sieve_data: Dict[Any, Any]):
        """Log transcript analysis."""
        sentiment = sieve_data.get("sentiment", "unknown")
        topics = sieve_data.get("topics", [])
        self.log_step(
            job_id,
            "ANALYSIS",
            f"Transcript analyzed - Sentiment: {sentiment}, Topics: {len(topics)}",
            {"sentiment": sentiment, "topics": topics}
        )
    
    def log_key_phrases(self, job_id: str, key_phrases: list):
        """Log key phrase extraction."""
        self.log_step(
            job_id,
            "KEY_PHRASES",
            f"Extracted {len(key_phrases)} key phrases for video generation",
            {"phrases": key_phrases, "phrase_count": len(key_phrases)}
        )
    
    def log_audio_generation(self, job_id: str, script: str, audio_path: str):
        """Log audio generation."""
        self.log_step(
            job_id,
            "AUDIO_GENERATION",
            f"Audio narration generated: {audio_path}",
            {"script_length": len(script), "audio_file": audio_path, "script_preview": script[:100] + "..." if len(script) > 100 else script}
        )
    
    def log_video_generation_start(self, job_id: str, phrase_count: int):
        """Log start of video generation."""
        self.log_step(
            job_id,
            "VIDEO_GENERATION_START",
            f"Starting generation of {phrase_count} video clips",
            {"video_count": phrase_count}
        )
    
    def log_video_clip_generated(self, job_id: str, clip_number: int, total_clips: int, prompt: str, video_path: str):
        """Log individual video clip generation."""
        self.log_step(
            job_id,
            "VIDEO_CLIP",
            f"Video clip {clip_number}/{total_clips} generated: {video_path}",
            {"clip_number": clip_number, "total_clips": total_clips, "prompt": prompt, "video_file": video_path}
        )
    
    def log_video_clip_error(self, job_id: str, clip_number: int, total_clips: int, prompt: str, error: str):
        """Log video clip generation error."""
        self.log_step(
            job_id,
            "VIDEO_CLIP_ERROR",
            f"Failed to generate video clip {clip_number}/{total_clips}: {error}",
            {"clip_number": clip_number, "total_clips": total_clips, "prompt": prompt, "error": str(error)}
        )
    
    def log_video_stitching(self, job_id: str, video_paths: list, final_video_path: str):
        """Log video stitching."""
        self.log_step(
            job_id,
            "VIDEO_STITCHING",
            f"Stitched {len(video_paths)} video clips into final video: {final_video_path}",
            {"input_videos": video_paths, "output_video": final_video_path, "clip_count": len(video_paths)}
        )
    
    def log_job_complete(self, job_id: str, final_video_path: str, success_count: int, total_count: int):
        """Log job completion."""
        self.log_step(
            job_id,
            "JOB_COMPLETE",
            f"Job completed! Generated {success_count}/{total_count} videos successfully. Final video: {final_video_path}",
            {"final_video": final_video_path, "success_count": success_count, "total_count": total_count, "success_rate": f"{(success_count/total_count)*100:.1f}%" if total_count > 0 else "0%"}
        )
    
    def log_job_error(self, job_id: str, error: str, step: str = "UNKNOWN"):
        """Log job error."""
        self.log_step(
            job_id,
            "JOB_ERROR",
            f"Job failed at step {step}: {error}",
            {"error": str(error), "failed_step": step}
        )


# Global logger instance
logger = JobLogger() 