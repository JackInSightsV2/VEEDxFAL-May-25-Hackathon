import os
import openai
import base64
import requests
import asyncio
import httpx

# Make sure OPENAI_API_KEY is set in the environment
openai.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")

def generate_image_with_openai(prompt: str, output_path: str = "openai_image.png") -> str:
    """Generate an image using OpenAI's image API (gpt-image-1) and save to output_path."""
    print(f"[OpenAI Image] Prompt: {prompt}")
    response = openai.images.generate(
        model="gpt-image-1",  # Always use gpt-image-1
        prompt=prompt,
        n=1,
        size="1024x1536"  # 2:3 aspect ratio, higher resolution
    )
    # print(f"[OpenAI Image] Raw response: {response}")
    image_url = getattr(response.data[0], 'url', None)
    print(f"[OpenAI Image] Image URL: {image_url}")
    if not image_url or not isinstance(image_url, str) or not image_url.startswith("http"):
        print(f"[OpenAI Image] ERROR: Invalid or missing image URL: {image_url}")
        # Try to fallback to b64_json if present
        b64_json = getattr(response.data[0], 'b64_json', None)
        if b64_json:
            print("[OpenAI Image] Fallback: Found b64_json, decoding and saving image.")
            image_data = base64.b64decode(b64_json)
            with open(output_path, "wb") as handler:
                handler.write(image_data)
            print(f"[OpenAI Image] Image saved to: {output_path}")
            return output_path
        print(f"[OpenAI Image] Full response for debugging: {response}")
        raise ValueError(f"OpenAI did not return a valid image URL or b64_json. See logs for details.")
    # Download the image
    img_data = requests.get(image_url).content
    with open(output_path, "wb") as handler:
        handler.write(img_data)
    print(f"[OpenAI Image] Image saved to: {output_path}")
    return output_path

async def async_generate_image_with_openai(prompt: str, output_path: str = "openai_image.png") -> str:
    """Async version: Generate an image using OpenAI's image API (gpt-image-1) and save to output_path."""
    print(f"[OpenAI Image Async] Prompt: {prompt}")
    
    # Run the blocking OpenAI API call in a thread
    import functools
    response = await asyncio.to_thread(
        functools.partial(
            openai.images.generate,
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size="1024x1536"
        )
    )
    
    image_url = getattr(response.data[0], 'url', None)
    print(f"[OpenAI Image Async] Image URL: {image_url}")
    
    if not image_url or not isinstance(image_url, str) or not image_url.startswith("http"):
        print(f"[OpenAI Image Async] ERROR: Invalid or missing image URL: {image_url}")
        # Try to fallback to b64_json if present
        b64_json = getattr(response.data[0], 'b64_json', None)
        if b64_json:
            print("[OpenAI Image Async] Fallback: Found b64_json, decoding and saving image.")
            image_data = base64.b64decode(b64_json)
            with open(output_path, "wb") as handler:
                handler.write(image_data)
            print(f"[OpenAI Image Async] Image saved to: {output_path}")
            return output_path
        print(f"[OpenAI Image Async] Full response for debugging: {response}")
        raise ValueError(f"OpenAI did not return a valid image URL or b64_json. See logs for details.")
    
    # Download the image asynchronously
    async with httpx.AsyncClient() as client:
        img_response = await client.get(image_url)
        img_response.raise_for_status()
        
        with open(output_path, "wb") as handler:
            handler.write(img_response.content)
        
        print(f"[OpenAI Image Async] Image saved to: {output_path}")
        return output_path 