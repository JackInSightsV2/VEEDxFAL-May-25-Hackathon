#!/usr/bin/env python3
"""
Interactive test script for the video generation pipeline.
Allows testing individual components with sample data.
"""

import os
import sys

# Load environment variables from .env file (like main.py does)
from dotenv import load_dotenv
load_dotenv()

from app.logger import logger
from app.whisper_transcriber import transcribe_video
from app.sievedata import analyze_transcript
from app.utils import beautify_transcript, extract_key_phrases
from app.elevenlabs import generate_voice
from app.fal import generate_videos_from_phrases, generate_video_from_text
from app.video_assembler import create_final_video

# Sample test data
SAMPLE_TRANSCRIPT = """
Today was an amazing day. I woke up early and went for a run in the park. 
The sunrise was absolutely beautiful with orange and pink colors painting the sky.
After my run, I stopped by the local coffee shop and got my favorite latte.
Then I spent the afternoon working on my art project in the studio.
The painting is finally coming together after weeks of work.
In the evening, I met up with friends for dinner at that new Italian restaurant.
We laughed so much and had the most delicious pasta.
"""

SAMPLE_SIEVE_DATA = {
    "sentiment": "positive",
    "topics": ["morning routine", "coffee", "art", "friends", "dinner"]
}

SAMPLE_KEY_PHRASES = [
    "A positive scene showing a peaceful morning run in a beautiful park with sunrise colors",
    "A positive scene about coffee: enjoying a warm latte at a cozy local coffee shop",
    "A positive scene about art: working on a painting in a creative studio space",
    "A positive scene about friends: having dinner and laughing at an Italian restaurant"
]

def check_environment_variables():
    """Check and display current environment variables."""
    print("\n🔑 Environment Variables Status:")
    print("=" * 50)
    
    # Check FAL API key
    fal_api_key = os.getenv("FAL_API_KEY")
    fal_key = os.getenv("FAL_KEY")
    if fal_api_key:
        print(f"✅ FAL_API_KEY: {fal_api_key[:10]}..." if len(fal_api_key) > 10 else f"✅ FAL_API_KEY: {fal_api_key}")
    else:
        print("❌ FAL_API_KEY: Not set")
    
    if fal_key:
        print(f"✅ FAL_KEY: {fal_key[:10]}..." if len(fal_key) > 10 else f"✅ FAL_KEY: {fal_key}")
    else:
        print("❌ FAL_KEY: Not set")
    
    # Check ElevenLabs API key
    eleven_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
    if eleven_key:
        print(f"✅ ELEVENLABS_API_KEY: {eleven_key[:10]}..." if len(eleven_key) > 10 else f"✅ ELEVENLABS_API_KEY: {eleven_key}")
    else:
        print("❌ ELEVENLABS_API_KEY: Not set")
    
    # Check Google credentials
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if google_creds:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS: {google_creds}")
    else:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS: Not set")
    
    # Auto-fix FAL_KEY if needed
    if fal_api_key and not fal_key:
        os.environ["FAL_KEY"] = fal_api_key
        print("🔧 Auto-mapped FAL_API_KEY to FAL_KEY")
    
    print()

class PipelineTester:
    def __init__(self):
        self.job_id = None
        self.test_results = {}
    
    def create_test_job(self):
        """Create a new test job."""
        self.job_id = logger.generate_job_id()
        logger.log_job_start(self.job_id, "Test")
        print(f"🧪 Created test job: {self.job_id}")
        print(f"📁 Job folder: {logger.get_job_folder(self.job_id)}")
        return self.job_id
    
    def test_transcript_analysis(self):
        """Test transcript analysis without needing a video file."""
        print("\n🔍 Testing Transcript Analysis...")
        print("=" * 50)
        
        try:
            # Use sample transcript
            print(f"Sample transcript: {SAMPLE_TRANSCRIPT[:100]}...")
            
            # Test analysis
            sieve_data = analyze_transcript(SAMPLE_TRANSCRIPT)
            logger.log_analysis(self.job_id, sieve_data)
            
            print(f"✅ Sentiment: {sieve_data.get('sentiment', 'unknown')}")
            print(f"✅ Topics: {sieve_data.get('topics', [])}")
            
            # Test key phrase extraction
            key_phrases = extract_key_phrases(SAMPLE_TRANSCRIPT, sieve_data, num_phrases=4)
            logger.log_key_phrases(self.job_id, key_phrases)
            
            print(f"✅ Generated {len(key_phrases)} key phrases:")
            for i, phrase in enumerate(key_phrases, 1):
                print(f"   {i}. {phrase}")
            
            self.test_results["transcript_analysis"] = True
            return True
            
        except Exception as e:
            print(f"❌ Transcript analysis failed: {e}")
            logger.log_job_error(self.job_id, str(e), "TRANSCRIPT_ANALYSIS")
            self.test_results["transcript_analysis"] = False
            return False
    
    def test_audio_generation(self):
        """Test audio generation with sample script."""
        print("\n🎵 Testing Audio Generation...")
        print("=" * 50)
        
        try:
            # Create sample script
            script = beautify_transcript(SAMPLE_TRANSCRIPT, "positive", SAMPLE_SIEVE_DATA)
            print(f"Sample script: {script[:100]}...")
            
            # Generate audio
            audio_path = generate_voice(script, self.job_id)
            logger.log_audio_generation(self.job_id, script, audio_path)
            
            if os.path.exists(audio_path):
                print(f"✅ Audio generated successfully: {audio_path}")
                file_size = os.path.getsize(audio_path)
                print(f"   File size: {file_size} bytes")
                self.test_results["audio_generation"] = True
                return audio_path
            else:
                print(f"❌ Audio file not found: {audio_path}")
                self.test_results["audio_generation"] = False
                return None
                
        except Exception as e:
            print(f"❌ Audio generation failed: {e}")
            logger.log_job_error(self.job_id, str(e), "AUDIO_GENERATION")
            self.test_results["audio_generation"] = False
            return None
    
    def test_single_video_generation(self):
        """Test generating a single video clip."""
        print("\n🎬 Testing Single Video Generation...")
        print("=" * 50)
        
        try:
            # Use first sample key phrase
            test_prompt = SAMPLE_KEY_PHRASES[0]
            print(f"Test prompt: {test_prompt}")
            
            # Generate single video
            video_path = generate_video_from_text(test_prompt, 0, self.job_id)
            
            if os.path.exists(video_path):
                print(f"✅ Video generated successfully: {video_path}")
                file_size = os.path.getsize(video_path)
                print(f"   File size: {file_size} bytes")
                self.test_results["single_video"] = True
                return [video_path]
            else:
                print(f"❌ Video file not found: {video_path}")
                self.test_results["single_video"] = False
                return []
                
        except Exception as e:
            print(f"❌ Single video generation failed: {e}")
            logger.log_job_error(self.job_id, str(e), "SINGLE_VIDEO")
            self.test_results["single_video"] = False
            return []
    
    def test_multiple_video_generation(self):
        """Test generating multiple video clips."""
        print("\n🎬 Testing Multiple Video Generation...")
        print("=" * 50)
        
        try:
            # Use sample key phrases (limit to 2 for testing)
            test_phrases = SAMPLE_KEY_PHRASES[:2]
            print(f"Generating {len(test_phrases)} videos...")
            
            # Generate videos
            video_paths = generate_videos_from_phrases(test_phrases, self.job_id)
            
            print(f"✅ Generated {len(video_paths)} out of {len(test_phrases)} videos")
            for i, path in enumerate(video_paths, 1):
                if os.path.exists(path):
                    file_size = os.path.getsize(path)
                    print(f"   {i}. {path} ({file_size} bytes)")
                else:
                    print(f"   {i}. {path} (file not found)")
            
            success = len(video_paths) > 0
            self.test_results["multiple_video"] = success
            return video_paths if success else []
            
        except Exception as e:
            print(f"❌ Multiple video generation failed: {e}")
            logger.log_job_error(self.job_id, str(e), "MULTIPLE_VIDEO")
            self.test_results["multiple_video"] = False
            return []
    
    def test_video_stitching(self, video_paths, audio_path):
        """Test video stitching with provided videos and audio."""
        print("\n🎞️ Testing Video Stitching...")
        print("=" * 50)
        
        if not video_paths:
            print("❌ No video paths provided for stitching")
            self.test_results["video_stitching"] = False
            return None
        
        if not audio_path or not os.path.exists(audio_path):
            print("❌ No audio file provided for stitching")
            self.test_results["video_stitching"] = False
            return None
        
        try:
            # Create final video
            final_video_path = create_final_video(video_paths, audio_path, self.job_id)
            logger.log_video_stitching(self.job_id, video_paths, final_video_path)
            
            if os.path.exists(final_video_path):
                file_size = os.path.getsize(final_video_path)
                print(f"✅ Final video created: {final_video_path}")
                print(f"   File size: {file_size} bytes")
                self.test_results["video_stitching"] = True
                return final_video_path
            else:
                print(f"❌ Final video not found: {final_video_path}")
                self.test_results["video_stitching"] = False
                return None
                
        except Exception as e:
            print(f"❌ Video stitching failed: {e}")
            logger.log_job_error(self.job_id, str(e), "VIDEO_STITCHING")
            self.test_results["video_stitching"] = False
            return None
    
    def test_transcription_with_file(self, video_file_path):
        """Test transcription with an actual video file."""
        print("\n🎤 Testing Video Transcription...")
        print("=" * 50)
        
        if not os.path.exists(video_file_path):
            print(f"❌ Video file not found: {video_file_path}")
            self.test_results["transcription"] = False
            return None
        
        try:
            # Copy video to job folder
            input_video_path = logger.get_job_file_path(self.job_id, "input_video.mp4")
            import shutil
            shutil.copy2(video_file_path, input_video_path)
            
            # Transcribe video
            transcript = transcribe_video(input_video_path, self.job_id)
            logger.log_transcription(self.job_id, transcript)
            
            print(f"✅ Transcription completed ({len(transcript)} characters)")
            print(f"   Preview: {transcript[:100]}...")
            
            self.test_results["transcription"] = True
            return transcript
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            logger.log_job_error(self.job_id, str(e), "TRANSCRIPTION")
            self.test_results["transcription"] = False
            return None
    
    def test_full_pipeline_with_sample_data(self):
        """Test the full pipeline using sample data (no real video)."""
        print("\n🚀 Testing Full Pipeline with Sample Data...")
        print("=" * 50)
        
        # Step 1: Analyze sample transcript
        if not self.test_transcript_analysis():
            return False
        
        # Step 2: Generate audio
        audio_path = self.test_audio_generation()
        if not audio_path:
            return False
        
        # Step 3: Generate videos (limited to 2 for testing)
        video_paths = self.test_multiple_video_generation()
        if not video_paths:
            return False
        
        # Step 4: Stitch everything together
        final_video = self.test_video_stitching(video_paths, audio_path)
        if not final_video:
            return False
        
        print("\n🎉 Full pipeline test completed successfully!")
        logger.log_job_complete(self.job_id, final_video, len(video_paths), len(SAMPLE_KEY_PHRASES))
        return True
    
    def print_results_summary(self):
        """Print a summary of all test results."""
        print("\n📊 Test Results Summary")
        print("=" * 50)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if self.job_id:
            print(f"Job folder: {logger.get_job_folder(self.job_id)}")

def show_menu():
    """Display the test menu."""
    print("\n🧪 Video Generation Pipeline Tester")
    print("=" * 50)
    print("1. Test Transcript Analysis (no video needed)")
    print("2. Test Audio Generation")
    print("3. Test Single Video Generation")
    print("4. Test Multiple Video Generation (2 clips)")
    print("5. Test Video Stitching (requires audio + videos)")
    print("6. Test Full Pipeline with Sample Data")
    print("7. Test Transcription with Video File")
    print("8. Show Test Results Summary")
    print("9. View Recent Logs")
    print("10. Check Environment Variables")
    print("0. Exit")
    print("=" * 50)

def main():
    """Main interactive test loop."""
    tester = PipelineTester()
    video_paths = []
    audio_path = None
    
    # Show environment status on startup
    check_environment_variables()
    
    while True:
        show_menu()
        choice = input("Enter your choice (0-10): ").strip()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        
        elif choice == "1":
            if not tester.job_id:
                tester.create_test_job()
            tester.test_transcript_analysis()
        
        elif choice == "2":
            if not tester.job_id:
                tester.create_test_job()
            audio_path = tester.test_audio_generation()
        
        elif choice == "3":
            if not tester.job_id:
                tester.create_test_job()
            single_video = tester.test_single_video_generation()
            if single_video:
                video_paths.extend(single_video)
        
        elif choice == "4":
            if not tester.job_id:
                tester.create_test_job()
            multiple_videos = tester.test_multiple_video_generation()
            if multiple_videos:
                video_paths = multiple_videos  # Replace previous videos
        
        elif choice == "5":
            if not tester.job_id:
                tester.create_test_job()
            if not video_paths:
                print("❌ No videos available. Generate videos first (option 3 or 4)")
            elif not audio_path:
                print("❌ No audio available. Generate audio first (option 2)")
            else:
                tester.test_video_stitching(video_paths, audio_path)
        
        elif choice == "6":
            tester.create_test_job()  # Always create new job for full test
            tester.test_full_pipeline_with_sample_data()
        
        elif choice == "7":
            if not tester.job_id:
                tester.create_test_job()
            video_file = input("Enter path to video file: ").strip()
            if video_file:
                tester.test_transcription_with_file(video_file)
        
        elif choice == "8":
            tester.print_results_summary()
        
        elif choice == "9":
            print("\n📜 Recent Logs:")
            print("-" * 30)
            try:
                with open("logs.txt", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    recent_lines = lines[-20:] if len(lines) > 20 else lines
                    print("".join(recent_lines))
            except FileNotFoundError:
                print("No log file found.")
        
        elif choice == "10":
            check_environment_variables()
        
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print("🚀 Starting Pipeline Tester...")
    
    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc() 