#!/usr/bin/env python3
"""
Test script for Azure UUID folder functionality.
This tests the enhanced Azure uploader with UUID folder organization.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.azure_uploader import upload_image, upload_video, upload_audio, upload_final_outputs
from app.logger import logger


def test_uuid_folders():
    """Test the UUID folder functionality for Azure uploads."""
    print("🔧 Testing Azure UUID Folder Functionality")
    print("=" * 50)
    
    # Create a test job ID
    job_id = logger.generate_job_id()
    print(f"📁 Generated test job ID: {job_id}")
    
    # Create test files if they don't exist
    test_image_path = "test_uuid_image.png"
    test_video_path = "test_uuid_video.mp4"
    test_audio_path = "test_uuid_audio.mp3"
    
    # Create a simple test image
    if not os.path.exists(test_image_path):
        try:
            from PIL import Image
            img = Image.new('RGB', (256, 256), color='blue')
            img.save(test_image_path)
            print(f"✅ Created test image: {test_image_path}")
        except ImportError:
            print("❌ PIL not available. Please create a test image manually.")
            return False
    
    # Create dummy video file (small text file for testing)
    if not os.path.exists(test_video_path):
        with open(test_video_path, "w") as f:
            f.write("This is a test video file for UUID folder testing.")
        print(f"✅ Created test video file: {test_video_path}")
    
    # Create dummy audio file (small text file for testing) 
    if not os.path.exists(test_audio_path):
        with open(test_audio_path, "w") as f:
            f.write("This is a test audio file for UUID folder testing.")
        print(f"✅ Created test audio file: {test_audio_path}")
    
    try:
        print(f"\n🔄 Testing uploads with job ID: {job_id}")
        
        # Test 1: Upload image with job ID
        print("\n1️⃣ Testing image upload with UUID folder...")
        image_url = upload_image(test_image_path, job_id=job_id)
        print(f"   Expected folder: {job_id}")
        print(f"   Actual URL: {image_url}")
        
        # Verify the URL contains the job ID as folder
        if f"/{job_id}/" in image_url:
            print("   ✅ Image uploaded to correct UUID folder")
        else:
            print("   ❌ Image NOT uploaded to UUID folder")
            return False
        
        # Test 2: Upload video with job ID
        print("\n2️⃣ Testing video upload with UUID folder...")
        video_url = upload_video(test_video_path, job_id=job_id, video_type="test")
        print(f"   Expected folder: {job_id}")
        print(f"   Actual URL: {video_url}")
        
        if f"/{job_id}/" in video_url and "test_" in video_url:
            print("   ✅ Video uploaded to correct UUID folder with type prefix")
        else:
            print("   ❌ Video NOT uploaded correctly")
            return False
        
        # Test 3: Upload audio with job ID
        print("\n3️⃣ Testing audio upload with UUID folder...")
        audio_url = upload_audio(test_audio_path, job_id=job_id)
        print(f"   Expected folder: {job_id}")
        print(f"   Actual URL: {audio_url}")
        
        if f"/{job_id}/" in audio_url:
            print("   ✅ Audio uploaded to correct UUID folder")
        else:
            print("   ❌ Audio NOT uploaded to UUID folder")
            return False
        
        # Test 4: Test final outputs upload with UUID naming
        print("\n4️⃣ Testing final outputs upload with UUID naming...")
        azure_urls = upload_final_outputs(job_id, test_video_path, test_audio_path)
        print(f"   Uploaded files: {list(azure_urls.keys())}")
        
        for key, url in azure_urls.items():
            print(f"   {key}: {url}")
            if f"/{job_id}/" in url:
                print(f"   ✅ {key} uploaded to correct UUID folder")
                
                # Check if final files use UUID in filename
                if key == "final_video_url":
                    if f"/{job_id}.mp4" in url:
                        print(f"   ✅ Final video uses UUID as filename: {job_id}.mp4")
                    else:
                        print(f"   ❌ Final video does NOT use UUID as filename")
                        return False
                elif key == "audio_url":
                    if f"/{job_id}_audio." in url:
                        print(f"   ✅ Final audio uses UUID as filename: {job_id}_audio.*")
                    else:
                        print(f"   ❌ Final audio does NOT use UUID as filename")
                        return False
            else:
                print(f"   ❌ {key} NOT uploaded to UUID folder")
                return False
        
        # Test 5: Test without job ID (should generate new UUID)
        print("\n5️⃣ Testing upload without job ID (auto-generated UUID)...")
        auto_image_url = upload_image(test_image_path)  # No job_id provided
        print(f"   Auto-generated URL: {auto_image_url}")
        
        # Extract the UUID from the URL
        url_parts = auto_image_url.split('/')
        if len(url_parts) >= 5:  # Should have container/uuid/filename structure
            auto_uuid = url_parts[-2]  # UUID should be second to last part
            print(f"   Auto-generated UUID: {auto_uuid}")
            
            # Check if it looks like a UUID (36 characters with dashes)
            if len(auto_uuid) == 36 and auto_uuid.count('-') == 4:
                print("   ✅ Auto-generated UUID folder looks correct")
            else:
                print("   ⚠️ Auto-generated UUID format might be incorrect")
        
        print("\n🎉 All Azure UUID folder tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Azure UUID folder test failed: {e}")
        return False
    
    finally:
        # Clean up test files
        for file_path in [test_image_path, test_video_path, test_audio_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"🧹 Cleaned up: {file_path}")
                except OSError:
                    print(f"⚠️ Could not clean up: {file_path}")


def test_azure_configuration():
    """Test that Azure configuration is properly set up."""
    print("\n🔧 Testing Azure Configuration")
    print("=" * 30)
    
    required_vars = [
        "AZURE_STORAGE_ACCOUNT",
        "AZURE_STORAGE_ACCOUNT_KEY", 
        "AZURE_STORAGE_CONTAINER"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: Not set")
        else:
            # Show first few characters for security
            display_value = value[:4] + "..." if len(value) > 4 else value
            print(f"✅ {var}: {display_value}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {missing_vars}")
        print("Please set these in your .env file.")
        return False
    else:
        print("\n✅ All Azure configuration variables are set!")
        return True


def main():
    """Main function to run all tests."""
    print("🧪 Azure UUID Folder Test Suite")
    print("=" * 60)
    
    # Test 1: Check Azure configuration
    if not test_azure_configuration():
        print("\n❌ Azure configuration test failed. Cannot proceed with upload tests.")
        return 1
    
    # Test 2: Test UUID folder functionality
    if not test_uuid_folders():
        print("\n❌ UUID folder functionality test failed.")
        return 1
    
    print("\n🎉 All tests passed! Azure UUID folder functionality is working correctly.")
    return 0


if __name__ == "__main__":
    exit(main()) 