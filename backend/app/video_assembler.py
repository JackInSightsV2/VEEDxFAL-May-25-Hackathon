"""Combine generated image and audio into a final video using ffmpeg."""

import subprocess


def create_video(image_path: str, audio_path: str, output_path: str = "final.mp4") -> str:
    """Assemble a video from the given image and audio and return the file path."""

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
