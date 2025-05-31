#!/usr/bin/env python3
"""
Video Duration Analyzer

This script takes an input video file and determines the play length 
of the video in seconds. This will be used later in the pipeline 
to generate audio that is the same length.

Usage:
    python video_duration.py <video_file_path>
    
Or import as a module:
    from video_duration import get_video_duration
    duration = get_video_duration("path/to/video.mp4")
"""

import cv2
import sys
import os
from typing import Optional


def get_video_duration(video_path: str) -> Optional[float]:
    """
    Get the duration of a video file in seconds.
    
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
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        
        # Check if video opened successfully
        if not cap.isOpened():
            print(f"Error: Could not open video file '{video_path}'.")
            return None
        
        # Get the frames per second (fps)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # Get the total number of frames
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        
        # Calculate duration in seconds
        duration = frame_count / fps if fps > 0 else 0
        
        # Release the video capture object
        cap.release()
        
        return duration
        
    except Exception as e:
        print(f"Error processing video file: {e}")
        return None


def main():
    """
    Main function for command-line usage.
    """
    if len(sys.argv) != 2:
        print("Usage: python video_duration.py <video_file_path>")
        print("Example: python video_duration.py input_video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    duration = get_video_duration(video_path)
    
    if duration is not None:
        print(f"Video duration: {duration:.2f} seconds")
        print(f"Video duration: {duration/60:.2f} minutes")
        return duration
    else:
        print("Failed to determine video duration.")
        sys.exit(1)


if __name__ == "__main__":
    main() 