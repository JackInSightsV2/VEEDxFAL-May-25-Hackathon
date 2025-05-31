#!/usr/bin/env python3
"""
Video Stitcher

A standalone script for stitching together multiple video files into a single output file.
Supports up to 10 videos, but typically used for 1-5 short video clips (often around 5 seconds each).

Usage:
    python video_stitcher.py
    
Or import as a module:
    from video_stitcher import stitch_videos
    output_path = stitch_videos(["video1.mp4", "video2.mp4"], "output.mp4")
"""

import os
import sys
import subprocess
import shutil
from typing import List, Optional
from pathlib import Path


def check_ffmpeg():
    """Check if ffmpeg is available."""
    ffmpeg_available = shutil.which("ffmpeg") is not None
    if not ffmpeg_available:
        print("❌ Error: ffmpeg is not installed or not found in PATH")
        print("Please install ffmpeg to use this script")
        print("Download from: https://ffmpeg.org/download.html")
        return False
    return True


def validate_video_files(video_paths: List[str]) -> List[str]:
    """
    Validate that video files exist and are accessible.
    
    Args:
        video_paths (List[str]): List of video file paths
        
    Returns:
        List[str]: List of valid video file paths
    """
    valid_paths = []
    
    for i, video_path in enumerate(video_paths, 1):
        if not os.path.exists(video_path):
            print(f"⚠️  Warning: Video {i} not found: {video_path}")
            continue
            
        if not os.path.isfile(video_path):
            print(f"⚠️  Warning: Video {i} is not a file: {video_path}")
            continue
            
        # Check file size
        file_size = os.path.getsize(video_path)
        if file_size == 0:
            print(f"⚠️  Warning: Video {i} is empty: {video_path}")
            continue
            
        print(f"✅ Video {i}: {video_path} ({file_size / (1024*1024):.2f} MB)")
        valid_paths.append(video_path)
    
    return valid_paths


def get_output_path(video_paths: List[str], custom_output: Optional[str] = None) -> str:
    """
    Determine the output path for the stitched video.
    Output will be in the same directory as the first input video.
    
    Args:
        video_paths (List[str]): List of input video paths
        custom_output (Optional[str]): Custom output filename
        
    Returns:
        str: Full path for the output video
    """
    if not video_paths:
        return "stitched_video.mp4"
    
    # Get directory of first video
    first_video_dir = os.path.dirname(os.path.abspath(video_paths[0]))
    
    if custom_output:
        output_filename = custom_output
    else:
        output_filename = "stitched_video.mp4"
    
    # Ensure output filename has .mp4 extension
    if not output_filename.lower().endswith('.mp4'):
        output_filename += '.mp4'
    
    output_path = os.path.join(first_video_dir, output_filename)
    
    # If file exists, add a number suffix
    base_path = output_path
    counter = 1
    while os.path.exists(output_path):
        name_part = os.path.splitext(base_path)[0]
        output_path = f"{name_part}_{counter}.mp4"
        counter += 1
    
    return output_path


def stitch_videos(video_paths: List[str], output_path: Optional[str] = None) -> str:
    """
    Stitch multiple video files together into a single output file.
    
    Args:
        video_paths (List[str]): List of video file paths to stitch together
        output_path (Optional[str]): Custom output path. If None, will be determined automatically
        
    Returns:
        str: Path to the output video file
        
    Raises:
        ValueError: If no valid video files provided
        RuntimeError: If ffmpeg command fails
    """
    # Validate inputs
    if not video_paths:
        raise ValueError("No video paths provided")
    
    if len(video_paths) > 10:
        print(f"⚠️  Warning: {len(video_paths)} videos provided, but maximum supported is 10")
        video_paths = video_paths[:10]
    
    # Check ffmpeg availability
    if not check_ffmpeg():
        raise RuntimeError("ffmpeg not available")
    
    # Validate video files
    valid_paths = validate_video_files(video_paths)
    if not valid_paths:
        raise ValueError("No valid video files found")
    
    print(f"\n🎬 Stitching {len(valid_paths)} video files...")
    
    # Handle single video case
    if len(valid_paths) == 1:
        src_path = valid_paths[0]
        if output_path is None:
            output_path = get_output_path(valid_paths, "stitched_video.mp4")
        
        print(f"📋 Single video detected, copying to output: {output_path}")
        shutil.copy2(src_path, output_path)
        print(f"✅ Video copied successfully!")
        return output_path
    
    # Determine output path
    if output_path is None:
        output_path = get_output_path(valid_paths, "stitched_video.mp4")
    
    print(f"📁 Output will be saved to: {output_path}")
    
    # Create temporary file list for ffmpeg
    output_dir = os.path.dirname(output_path)
    video_list_path = os.path.join(output_dir, "temp_video_list.txt")
    
    try:
        # Write video list file
        with open(video_list_path, "w", encoding="utf-8") as f:
            for video_path in valid_paths:
                # Use absolute paths and escape them properly
                abs_path = os.path.abspath(video_path)
                # Escape backslashes for Windows paths
                escaped_path = abs_path.replace("\\", "/") if os.name == 'nt' else abs_path
                f.write(f"file '{escaped_path}'\n")
        
        print(f"📝 Created temporary file list: {video_list_path}")
        
        # Build ffmpeg command
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-f", "concat",
            "-safe", "0",
            "-i", video_list_path,
            "-c", "copy",  # Copy streams without re-encoding (faster)
            output_path
        ]
        
        print(f"🔧 Running ffmpeg command...")
        print(f"   Command: {' '.join(ffmpeg_cmd[:8])}... {output_path}")
        
        # Execute ffmpeg command
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if result.returncode != 0:
            error_msg = f"ffmpeg failed with return code {result.returncode}"
            if result.stderr:
                error_msg += f"\nError output: {result.stderr}"
            raise RuntimeError(error_msg)
        
        # Verify output file was created
        if not os.path.exists(output_path):
            raise RuntimeError(f"Output file was not created: {output_path}")
        
        output_size = os.path.getsize(output_path)
        print(f"✅ Video stitching completed successfully!")
        print(f"📁 Output file: {output_path}")
        print(f"📏 Output size: {output_size / (1024*1024):.2f} MB")
        
        return output_path
        
    finally:
        # Clean up temporary file
        if os.path.exists(video_list_path):
            try:
                os.remove(video_list_path)
                print(f"🧹 Cleaned up temporary file: {video_list_path}")
            except OSError as e:
                print(f"⚠️  Warning: Could not remove temporary file {video_list_path}: {e}")


def interactive_mode():
    """Run the script in interactive mode, asking user for video files."""
    print("🎬 Video Stitcher - Interactive Mode")
    print("=" * 50)
    
    video_paths = []
    
    while len(video_paths) < 10:
        video_num = len(video_paths) + 1
        
        if video_num == 1:
            prompt = f"Enter path to video file {video_num}: "
        else:
            prompt = f"Enter path to video file {video_num} (or press Enter to finish): "
        
        video_path = input(prompt).strip()
        
        # Remove quotes if present
        if video_path.startswith('"') and video_path.endswith('"'):
            video_path = video_path[1:-1]
        elif video_path.startswith("'") and video_path.endswith("'"):
            video_path = video_path[1:-1]
        
        # If empty and we have at least one video, break
        if not video_path and len(video_paths) > 0:
            break
        
        # If empty and no videos yet, require at least one
        if not video_path and len(video_paths) == 0:
            print("❌ Please provide at least one video file")
            continue
        
        video_paths.append(video_path)
    
    if not video_paths:
        print("❌ No video files provided")
        return
    
    # Ask for custom output name
    custom_output = input("\nEnter output filename (or press Enter for 'stitched_video.mp4'): ").strip()
    if custom_output:
        # Remove quotes if present
        if custom_output.startswith('"') and custom_output.endswith('"'):
            custom_output = custom_output[1:-1]
        elif custom_output.startswith("'") and custom_output.endswith("'"):
            custom_output = custom_output[1:-1]
    
    try:
        output_path = stitch_videos(video_paths, custom_output if custom_output else None)
        print(f"\n🎉 Success! Stitched video saved to: {output_path}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


def main():
    """Main function for command line usage."""
    if len(sys.argv) == 1:
        # No arguments provided, run in interactive mode
        return interactive_mode()
    
    elif len(sys.argv) >= 2:
        # Video files provided as arguments
        video_paths = sys.argv[1:]
        
        try:
            output_path = stitch_videos(video_paths)
            print(f"\n🎉 Success! Stitched video saved to: {output_path}")
            return 0
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return 1
    
    else:
        print("Usage:")
        print("  python video_stitcher.py                    # Interactive mode")
        print("  python video_stitcher.py video1.mp4 video2.mp4 ...  # Direct mode")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 