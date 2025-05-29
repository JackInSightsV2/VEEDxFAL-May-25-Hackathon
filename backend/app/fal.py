"""Image generation module using FAL API."""

import os
import requests


def generate_image(prompt: str) -> str:
    """Generate an image based on the prompt and return the image path."""
    headers = {"Authorization": f"Bearer {os.getenv('FAL_API_KEY')}"}
    payload = {"prompt": prompt, "num_images": 1}
    response = requests.post(
        "https://api.fal.ai/generate", json=payload, headers=headers
    )
    image_url = response.json()["images"][0]
    image_path = "output.jpg"
    with open(image_path, "wb") as f:
        f.write(requests.get(image_url).content)
    return image_path
