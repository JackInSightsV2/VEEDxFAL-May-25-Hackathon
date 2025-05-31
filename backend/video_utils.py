#!/usr/bin/env python3
"""
Video Utilities

A unified module for video processing utilities including duration analysis.
This module tries multiple methods for maximum compatibility with different video formats.

Usage:
    from video_utils import get_video_duration
    duration = get_video_duration("path/to/video.mp4")
"""

import os
import sys
import subprocess
import shutil
from typing import Optional

# Try to import required libraries
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    from moviepy.editor import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False

# Check for ffmpeg/ffprobe availability
HAS_FFMPEG = shutil.which("ffprobe") is not None or shutil.which("ffmpeg") is not None


def get_video_duration_opencv(video_path: str) -> Optional[float]:
    """
    Get video duration using OpenCV.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        Optional[float]: Duration in seconds, or None if error
    """
    if not HAS_OPENCV:
        return None
        
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        return duration
        
    except Exception:
        return None


def get_video_duration_moviepy(video_path: str) -> Optional[float]:
    """
    Get video duration using MoviePy.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        Optional[float]: Duration in seconds, or None if error
    """
    if not HAS_MOVIEPY:
        return None
        
    try:
        with VideoFileClip(video_path) as clip:
            return clip.duration
    except Exception:
        return None


def get_video_duration_ffmpeg(video_path: str) -> Optional[float]:
    """
    Get video duration using ffprobe/ffmpeg.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        Optional[float]: Duration in seconds, or None if error
    """
    if not HAS_FFMPEG:
        return None
    
    try:
        # Try ffprobe first (more appropriate for metadata extraction)
        ffprobe_cmd = shutil.which("ffprobe")
        if ffprobe_cmd:
            cmd = [
                ffprobe_cmd,
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
        else:
            # Fallback to ffmpeg
            ffmpeg_cmd = shutil.which("ffmpeg")
            if not ffmpeg_cmd:
                return None
            
            cmd = [
                ffmpeg_cmd,
                "-i", video_path,
                "-f", "null", "-"
            ]
        
        # Execute command
        if ffprobe_cmd:
            # ffprobe returns duration directly
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0 and result.stdout.strip():
                duration = float(result.stdout.strip())
                return duration
        else:
            # ffmpeg returns info in stderr
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Parse duration from ffmpeg output
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    # Extract duration like "Duration: 00:01:23.45"
                    duration_str = line.split('Duration:')[1].split(',')[0].strip()
                    # Parse HH:MM:SS.ms format
                    time_parts = duration_str.split(':')
                    if len(time_parts) == 3:
                        hours = float(time_parts[0])
                        minutes = float(time_parts[1])
                        seconds = float(time_parts[2])
                        total_seconds = hours * 3600 + minutes * 60 + seconds
                        return total_seconds
        
        return None
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError, IndexError):
        return None
    except Exception:
        return None


def get_video_duration(video_path: str, method: str = "auto") -> Optional[float]:
    """
    Get the duration of a video file in seconds.
    Tries multiple methods for maximum compatibility.
    
    Args:
        video_path (str): Path to the video file
        method (str): Method to use ("opencv", "moviepy", "ffmpeg", or "auto")
        
    Returns:
        Optional[float]: Duration in seconds, or None if error
    """
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        return None
    
    duration = None
    
    if method == "opencv" or method == "auto":
        duration = get_video_duration_opencv(video_path)
        if duration is not None:
            return duration
    
    if method == "moviepy" or method == "auto":
        duration = get_video_duration_moviepy(video_path)
        if duration is not None:
            return duration
    
    if method == "ffmpeg" or method == "auto":
        duration = get_video_duration_ffmpeg(video_path)
        if duration is not None:
            return duration
    
    # If we get here, all methods failed
    if method == "auto":
        available_methods = []
        if HAS_OPENCV:
            available_methods.append("opencv")
        if HAS_MOVIEPY:
            available_methods.append("moviepy")
        if HAS_FFMPEG:
            available_methods.append("ffmpeg")
        
        if not available_methods:
            print("Error: No video processing libraries/tools available.")
            print("Install with: pip install opencv-python moviepy")
            print("Or install ffmpeg: https://ffmpeg.org/download.html")
        else:
            print(f"Error: Could not determine video duration using available methods: {available_methods}")
    
    return None


def format_duration(duration_seconds: float) -> str:
    """
    Format duration in a human-readable way.
    
    Args:
        duration_seconds (float): Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    seconds = duration_seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"
    else:
        return f"{minutes:02d}:{seconds:05.2f}"


def get_available_methods() -> list:
    """
    Get a list of available video duration detection methods.
    
    Returns:
        list: List of available method names
    """
    methods = []
    if HAS_OPENCV:
        methods.append("opencv")
    if HAS_MOVIEPY:
        methods.append("moviepy")
    if HAS_FFMPEG:
        methods.append("ffmpeg")
    return methods


def main():
    """
    Main function for command-line usage.
    """
    if len(sys.argv) < 2:
        print("Usage: python video_utils.py <video_file_path> [method]")
        print("Methods: opencv, moviepy, ffmpeg, auto (default)")
        print("Example: python video_utils.py input_video.mp4 auto")
        print(f"Available methods: {get_available_methods()}")
        sys.exit(1)
    
    video_path = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    print(f"Available methods: {get_available_methods()}")
    print(f"Using method: {method}")
    
    duration = get_video_duration(video_path, method)
    
    if duration is not None:
        print(f"Video duration: {duration:.2f} seconds")
        print(f"Video duration: {format_duration(duration)}")
        print(f"Video duration: {duration/60:.2f} minutes")
        return duration
    else:
        print("Failed to determine video duration.")
        sys.exit(1)


if __name__ == "__main__":
    main() 