#!/usr/bin/env python3
"""
Simple test script demonstrating the new VEO2 image-to-video functionality.
This matches the boilerplate code provided by the user.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.fal import generate_video_from_image
from app.azure_uploader import upload_image

def test_veo2_image_to_video():
    """Test the VEO2 image-to-video model with a sample image and prompt."""
    print("🎬 Testing VEO2 Image-to-Video Generation")
    print("=" * 50)
    
    # Create a simple test image if it doesn't exist
    image_path = "test_veo2_image.png"
    if not os.path.exists(image_path):
        try:
            from PIL import Image
            # Create a simple red square image
            img = Image.new('RGB', (512, 512), color='red')
            img.save(image_path)
            print(f"✅ Created test image: {image_path}")
        except ImportError:
            print("❌ PIL not available. Please create a test image manually.")
            return
    
    # Test prompt (matching the user's boilerplate example)
    prompt = "A lego chef cooking eggs"
    
    print(f"📸 Image: {image_path}")
    print(f"📝 Prompt: {prompt}")
    print("🚀 Generating video with VEO2...")
    
    try:
        # Generate video using the new VEO2 model
        video_path = generate_video_from_image(image_path, prompt, video_id=0)
        
        if os.path.exists(video_path):
            print(f"✅ Video generated successfully: {video_path}")
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            print(f"📊 File size: {file_size:.2f} MB")
        else:
            print(f"❌ Video file not found: {video_path}")
            
    except Exception as e:
        print(f"❌ Error generating video: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 VEO2 Image-to-Video Test Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Please run this script from the backend directory")
        print("Current directory:", os.getcwd())
        sys.exit(1)
    
    # Check if FAL_KEY is set
    if not os.getenv("FAL_KEY") and not os.getenv("FAL_API_KEY"):
        print("❌ FAL API key not found. Please set FAL_KEY or FAL_API_KEY in your .env file")
        sys.exit(1)
    
    test_veo2_image_to_video() 