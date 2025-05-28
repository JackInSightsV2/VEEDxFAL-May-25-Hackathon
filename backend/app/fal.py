"""Image generation module using FAL API."""

import os
from dotenv import load_dotenv

load_dotenv()

FAL_API_KEY = os.getenv("FAL_API_KEY")


def generate_image(prompt: str) -> str:
    """Generate an image based on the prompt and return the image path."""
    # TODO: integrate with FAL API using FAL_API_KEY
    return "path/to/generated_image.png"
