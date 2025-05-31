#!/usr/bin/env python3
"""
Test script to verify backend endpoints work correctly for frontend integration.
Run this after starting the backend server to test the API endpoints.
"""

import requests
import time
import json

# Backend URL - change this if running on different host/port
BACKEND_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint to see available endpoints."""
    print("\n🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working")
            print(f"📋 Available endpoints: {len(data.get('endpoints', []))}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_text_generation():
    """Test text-based video generation (without actually generating)."""
    print("\n🔍 Testing text generation endpoint...")
    
    # Test data matching frontend format
    test_data = {
        'text': 'Today was a great day! I went for a walk in the park and enjoyed the sunshine.',
        'gender': 'female',
        'age_group': '26-35',
        'visual_style': 'Studio Ghibli',
        'mood': 'Reflective'
    }
    
    try:
        # Note: This will actually start a job, so we're just testing the endpoint accepts the data
        print(f"📤 Sending test data: {test_data}")
        print("⚠️  Note: This will start an actual job - cancel if you don't want to use API credits")
        
        # Uncomment the next lines to actually test (will use API credits):
        # response = requests.post(f"{BACKEND_URL}/generate-from-text", data=test_data)
        # if response.status_code == 200:
        #     result = response.json()
        #     print(f"✅ Text generation started: Job ID {result.get('job_id')}")
        #     return result.get('job_id')
        # else:
        #     print(f"❌ Text generation failed: {response.status_code}")
        #     print(f"Response: {response.text}")
        #     return None
        
        print("🔄 Skipping actual API call to avoid using credits")
        return "test-job-id"
        
    except Exception as e:
        print(f"❌ Text generation error: {e}")
        return None

def test_status_endpoint(job_id):
    """Test the status endpoint."""
    print(f"\n🔍 Testing status endpoint with job ID: {job_id}")
    try:
        response = requests.get(f"{BACKEND_URL}/status/{job_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working: {data.get('status', 'unknown')}")
            print(f"📊 Progress: {data.get('progress', 0)}%")
            return True
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting backend integration tests...\n")
    
    # Test basic endpoints
    if not test_health_endpoint():
        print("❌ Backend not responding. Make sure it's running on http://localhost:8000")
        return
    
    if not test_root_endpoint():
        print("❌ Root endpoint failed")
        return
    
    # Test text generation endpoint structure
    job_id = test_text_generation()
    
    # Test status endpoint
    if job_id:
        test_status_endpoint(job_id)
    
    print("\n🎉 Integration tests completed!")
    print("\n📝 Next steps:")
    print("1. Create .env.local in frontend/ with: NEXT_PUBLIC_BACKEND_URL=http://localhost:8000")
    print("2. Start frontend with: cd frontend && npm run dev")
    print("3. Test the full flow at http://localhost:3000")

if __name__ == "__main__":
    main() 