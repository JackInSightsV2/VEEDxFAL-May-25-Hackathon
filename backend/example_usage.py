#!/usr/bin/env python3
"""
Example Usage: Video Duration for Audio Generation Pipeline

This script demonstrates how to use the video duration utilities
in your AI Memory Journal pipeline to generate audio of matching length.
"""

from video_utils import get_video_duration, format_duration


def prepare_audio_generation(video_path: str) -> dict:
    """
    Prepare parameters for audio generation based on video duration.
    
    Args:
        video_path (str): Path to the input video file
        
    Returns:
        dict: Parameters for audio generation including duration
    """
    # Get video duration
    duration = get_video_duration(video_path)
    
    if duration is None:
        raise ValueError(f"Could not determine duration for video: {video_path}")
    
    # Prepare audio generation parameters
    audio_params = {
        "target_duration_seconds": duration,
        "target_duration_minutes": duration / 60,
        "formatted_duration": format_duration(duration),
        "video_path": video_path,
        # Add buffer time if needed (optional)
        "duration_with_buffer": duration + 1.0,  # Add 1 second buffer
    }
    
    return audio_params


def example_pipeline(video_path: str):
    """
    Example pipeline showing how to integrate video duration analysis.
    """
    print(f"Processing video: {video_path}")
    
    try:
        # Step 1: Get video duration
        audio_params = prepare_audio_generation(video_path)
        print(f"✅ Video duration determined: {audio_params['formatted_duration']}")
        
        # Step 2: Use duration for audio generation (placeholder)
        print(f"🎵 Preparing to generate {audio_params['target_duration_seconds']:.2f} seconds of audio...")
        
        # Here you would call your ElevenLabs API or other audio generation
        # Example:
        # audio_content = generate_audio_with_elevenlabs(
        #     script=processed_script,
        #     duration=audio_params['target_duration_seconds']
        # )
        
        print(f"✅ Audio generation parameters ready:")
        print(f"   - Target duration: {audio_params['target_duration_seconds']:.2f}s")
        print(f"   - Formatted time: {audio_params['formatted_duration']}")
        print(f"   - With buffer: {audio_params['duration_with_buffer']:.2f}s")
        
        return audio_params
        
    except Exception as e:
        print(f"❌ Error in pipeline: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python example_usage.py <video_file_path>")
        print("Example: python example_usage.py input_video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    result = example_pipeline(video_path)
    
    if result:
        print("\n🎉 Pipeline preparation completed successfully!")
    else:
        print("\n💥 Pipeline preparation failed!")
        sys.exit(1) 