#!/usr/bin/env python3
"""
Debug script to test UUID generation and ensure each call produces unique IDs.
"""

import uuid
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.logger import logger

def test_uuid_generation():
    """Test that UUID generation produces unique IDs."""
    print("DEBUG: Testing UUID generation...")
    print("=" * 50)
    
    # Test standard uuid.uuid4()
    print("\n1. Testing uuid.uuid4() directly:")
    uuids = []
    for i in range(10):
        new_uuid = str(uuid.uuid4())
        uuids.append(new_uuid)
        print(f"   UUID {i+1}: {new_uuid}")
    
    print(f"\n   Generated {len(uuids)} UUIDs")
    print(f"   Unique UUIDs: {len(set(uuids))}")
    print(f"   All unique: {len(uuids) == len(set(uuids))}")
    
    # Test logger.generate_job_id()
    print("\n2. Testing logger.generate_job_id():")
    job_ids = []
    for i in range(10):
        job_id = logger.generate_job_id()
        job_ids.append(job_id)
        print(f"   Job ID {i+1}: {job_id}")
        print(f"   Job folder: {logger.get_job_folder(job_id)}")
    
    print(f"\n   Generated {len(job_ids)} job IDs")
    print(f"   Unique job IDs: {len(set(job_ids))}")
    print(f"   All unique: {len(job_ids) == len(set(job_ids))}")
    
    # Test if job folders would be created properly
    print("\n3. Testing job folder creation:")
    test_job_id = logger.generate_job_id()
    job_folder = logger.create_job_folder(test_job_id)
    print(f"   Test job ID: {test_job_id}")
    print(f"   Job folder created: {job_folder}")
    print(f"   Folder exists: {os.path.exists(job_folder)}")
    
    # Test file paths
    test_file_path = logger.get_job_file_path(test_job_id, "test_file.txt")
    print(f"   Test file path: {test_file_path}")
    
    # Write a test file
    with open(test_file_path, 'w') as f:
        f.write(f"Test file for job {test_job_id}")
    
    print(f"   Test file created: {os.path.exists(test_file_path)}")
    
    return True

def test_api_simulation():
    """Simulate multiple API calls to see if job IDs are unique."""
    print("\n\nAPI: Simulating multiple API calls...")
    print("=" * 50)
    
    api_jobs = []
    
    for request_num in range(5):
        print(f"\n--- API Request {request_num + 1} ---")
        
        # Simulate what happens in main.py
        job_id = logger.generate_job_id()
        logger.log_job_start(job_id, "Reflective")
        
        print(f"Generated job ID: {job_id}")
        print(f"Job folder: {logger.get_job_folder(job_id)}")
        
        # Create a test file in the job folder
        test_file = logger.get_job_file_path(job_id, f"request_{request_num + 1}.txt")
        with open(test_file, 'w') as f:
            f.write(f"This is from API request {request_num + 1}\nJob ID: {job_id}")
        
        print(f"Created test file: {test_file}")
        
        api_jobs.append(job_id)
    
    print(f"\nSUMMARY:")
    print(f"   Total API requests: {len(api_jobs)}")
    print(f"   Unique job IDs: {len(set(api_jobs))}")
    print(f"   All unique: {len(api_jobs) == len(set(api_jobs))}")
    
    if len(api_jobs) != len(set(api_jobs)):
        print("ERROR: Some job IDs were reused!")
        duplicates = [job_id for job_id in api_jobs if api_jobs.count(job_id) > 1]
        print(f"   Duplicate job IDs: {set(duplicates)}")
    else:
        print("SUCCESS: All job IDs were unique")
    
    return api_jobs

if __name__ == "__main__":
    print("UUID Generation Debug Tool")
    print("=" * 50)
    
    try:
        test_uuid_generation()
        api_jobs = test_api_simulation()
        
        print("\n\nSUCCESS: Debug test completed!")
        print("If you're still seeing duplicate job IDs in your API,")
        print("the issue may be elsewhere (e.g., client-side caching,")
        print("browser state, or server process management).")
        
    except Exception as e:
        print(f"\nERROR: Debug test failed: {e}")
        import traceback
        traceback.print_exc() 