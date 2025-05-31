#!/usr/bin/env python3
"""
Video Duration Analyzer (MoviePy Version)

Alternative implementation using MoviePy library for video duration analysis.
This can be more reliable for certain video formats and codecs.

Usage:
    python video_duration_moviepy.py <video_file_path>
    
Or import as a module:
    from video_duration_moviepy import get_video_duration_moviepy
    duration = get_video_duration_moviepy("path/to/video.mp4")
"""

import sys
import os
from typing import Optional

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    print("MoviePy is not installed. Install it with: pip install moviepy")
    sys.exit(1)


def get_video_duration_moviepy(video_path: str) -> Optional[float]:
    """
    Get the duration of a video file in seconds using MoviePy.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        Optional[float]: Duration in seconds, or None if error
    """
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found.")
        return None
    
    try:
        # Load the video file
        with VideoFileClip(video_path) as clip:
            duration = clip.duration
            return duration
            
    except Exception as e:
        print(f"Error processing video file: {e}")
        return None


def main():
    """
    Main function for command-line usage.
    """
    if len(sys.argv) != 2:
        print("Usage: python video_duration_moviepy.py <video_file_path>")
        print("Example: python video_duration_moviepy.py input_video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    duration = get_video_duration_moviepy(video_path)
    
    if duration is not None:
        print(f"Video duration: {duration:.2f} seconds")
        print(f"Video duration: {duration/60:.2f} minutes")
        return duration
    else:
        print("Failed to determine video duration.")
        sys.exit(1)


if __name__ == "__main__":
    main() 