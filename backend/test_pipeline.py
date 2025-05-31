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
from app.utils import beautify_transcript, extract_key_phrases
from app.elevenlabs import generate_voice
from app.fal import generate_videos_from_phrases, generate_video_from_text, generate_video_from_image, generate_blog_avatar_video, async_generate_video_from_image
from app.video_assembler import create_final_video, add_audio_to_video
from app.openai_image import generate_image_with_openai, async_generate_image_with_openai
from app.piwigo_uploader import upload_image
from app.gcp_nlp import analyze_transcript, get_sentiment_description

# Import video duration utilities
from video_utils import (
    get_video_duration_opencv,
    get_video_duration_moviepy, 
    get_video_duration_ffmpeg,
    get_video_duration,
    get_available_methods,
    format_duration,
    HAS_OPENCV,
    HAS_MOVIEPY,
    HAS_FFMPEG
)

# Import standalone video stitcher
from video_stitcher import stitch_videos

# Import OpenAI for text generation
import openai
# Import asyncio for concurrent processing
import asyncio

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

# This will now be generated dynamically using GCP NLP
# SAMPLE_SENTIMENT_DATA = {
#     "sentiment": "positive",
#     "topics": ["morning routine", "coffee", "art", "friends", "dinner"]
# }

# Key phrases are now generated dynamically based on analysis
# SAMPLE_KEY_PHRASES = [
#     "A positive scene showing a peaceful morning run in a beautiful park with sunrise colors",
#     "A positive scene about coffee: enjoying a warm latte at a cozy local coffee shop",
#     "A positive scene about art: working on a painting in a creative studio space",
#     "A positive scene about friends: having dinner and laughing at an Italian restaurant"
# ]

SAMPLE_GENDER = "male"
SAMPLE_AGE_GROUP = "20-30"
SAMPLE_VISUAL_STYLE = "Studio Ghibli"

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
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")
    if openai_key:
        print(f"✅ OPENAI_API_KEY: {openai_key[:10]}..." if len(openai_key) > 10 else f"✅ OPENAI_API_KEY: {openai_key}")
    else:
        print("❌ OPENAI_API_KEY: Not set")
    
    # Auto-fix FAL_KEY if needed
    if fal_api_key and not fal_key:
        os.environ["FAL_KEY"] = fal_api_key
        print("🔧 Auto-mapped FAL_API_KEY to FAL_KEY")
    
    print()

class PipelineTester:
    def __init__(self):
        self.job_id = None
        self.test_results = {}
        self.sentiment_data = None  # Will be populated by transcript analysis
    
    def create_test_job(self):
        """Create a new test job."""
        self.job_id = logger.generate_job_id()
        logger.log_job_start(self.job_id, "Test")
        print(f"🧪 Created test job: {self.job_id}")
        print(f"📁 Job folder: {logger.get_job_folder(self.job_id)}")
        return self.job_id
    
    def test_transcript_analysis(self):
        """Test transcript analysis using GCP NLP instead of hardcoded data."""
        print("\n🔍 Testing Transcript Analysis with GCP NLP...")
        print("=" * 50)
        
        try:
            # Use sample transcript
            print(f"Sample transcript: {SAMPLE_TRANSCRIPT[:100]}...")
            
            # Analyze transcript using GCP NLP
            print("🤖 Analyzing transcript with Google Cloud Natural Language API...")
            sentiment_data = analyze_transcript(SAMPLE_TRANSCRIPT)
            
            # Log the analysis
            logger.log_analysis(self.job_id, sentiment_data)
            
            # Display results
            sentiment = sentiment_data.get('sentiment', 'unknown')
            sentiment_score = sentiment_data.get('sentiment_score', 0.0)
            topics = sentiment_data.get('topics', [])
            entities = sentiment_data.get('entities', [])
            
            print(f"✅ Sentiment: {sentiment} (score: {sentiment_score:.2f})")
            print(f"✅ Topics ({len(topics)}): {topics}")
            
            if entities:
                print(f"✅ Key Entities ({len(entities)}):")
                for entity in entities[:5]:  # Show top 5 entities
                    print(f"   - {entity['name']} ({entity['type']}, salience: {entity['salience']:.2f})")
            
            # Test key phrase extraction with dynamic analysis
            key_phrases = extract_key_phrases(
                SAMPLE_TRANSCRIPT, sentiment_data, num_phrases=4,
                gender=SAMPLE_GENDER, age_group=SAMPLE_AGE_GROUP, visual_style=SAMPLE_VISUAL_STYLE
            )
            logger.log_key_phrases(self.job_id, key_phrases)
            
            print(f"✅ Generated {len(key_phrases)} key phrases:")
            for i, phrase in enumerate(key_phrases, 1):
                print(f"   {i}. {phrase}")
            
            # Store the analysis result for use in other tests
            self.sentiment_data = sentiment_data
            self.test_results["transcript_analysis"] = True
            return True
            
        except Exception as e:
            print(f"❌ Transcript analysis failed: {e}")
            logger.log_job_error(self.job_id, str(e), "TRANSCRIPT_ANALYSIS")
            self.test_results["transcript_analysis"] = False
            return False
    
    def ensure_transcript_analysis(self):
        """Ensure transcript analysis has been run, or run it now."""
        if self.sentiment_data is None:
            print("⚠️  Running transcript analysis first...")
            self.test_transcript_analysis()
        return self.sentiment_data is not None
    
    def test_audio_generation(self):
        """Test audio generation with sample script."""
        print("\n🎵 Testing Audio Generation...")
        print("=" * 50)
        
        try:
            # Ensure we have analysis data
            if not self.ensure_transcript_analysis():
                print("❌ Cannot generate audio without transcript analysis")
                self.test_results["audio_generation"] = False
                return None
            
            # Create sample script
            script = beautify_transcript(
                SAMPLE_TRANSCRIPT, "positive", self.sentiment_data,
                gender=SAMPLE_GENDER, age_group=SAMPLE_AGE_GROUP, visual_style=SAMPLE_VISUAL_STYLE
            )
            print(f"Sample script: {script[:100]}...")
            
            # Generate audio
            audio_path = generate_voice(script, self.job_id, gender=SAMPLE_GENDER)
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
    
    def test_elevenlabs_audio_generation(self):
        """Test ElevenLabs audio generation with simple text and detailed debugging."""
        print("\n🎤 Testing ElevenLabs Audio Generation (Standalone)...")
        print("=" * 50)
        
        # Check API key first
        api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
        if not api_key:
            print("❌ ElevenLabs API key not found!")
            print("   Please set ELEVENLABS_API_KEY or ELEVEN_API_KEY in your .env file")
            self.test_results["elevenlabs_audio"] = False
            return None
        
        print(f"✅ ElevenLabs API key found: {api_key[:10]}...")
        
        # Use simple test text
        test_text = "Hello, this is a test of the ElevenLabs audio generation system. The weather is beautiful today!"
        print(f"📝 Test text: {test_text}")
        
        try:
            # Test audio generation
            audio_path = generate_voice(test_text, self.job_id, gender="female")
            
            if audio_path and os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"✅ ElevenLabs audio test successful!")
                print(f"   Audio file: {audio_path}")
                print(f"   File size: {file_size} bytes ({file_size / 1024:.2f} KB)")
                
                # Test with male voice too
                print(f"\n🎤 Testing male voice...")
                male_audio_path = generate_voice("This is a test with a male voice.", self.job_id, gender="male")
                if male_audio_path and os.path.exists(male_audio_path):
                    print(f"✅ Male voice test successful: {male_audio_path}")
                else:
                    print(f"⚠️ Male voice test failed")
                
                # Try to get audio duration using ffprobe
                try:
                    import subprocess
                    ffprobe_cmd = [
                        "ffprobe",
                        "-v", "quiet", 
                        "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        audio_path
                    ]
                    
                    result = subprocess.run(
                        ffprobe_cmd,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        duration = float(result.stdout.strip())
                        print(f"   Duration: {duration:.2f} seconds")
                    else:
                        print("   Duration: Could not determine")
                        
                except Exception as e:
                    print(f"   Duration check failed: {e}")
                
                self.test_results["elevenlabs_audio"] = True
                return audio_path
            else:
                print("❌ ElevenLabs audio file was not created or is empty")
                self.test_results["elevenlabs_audio"] = False
                return None
                
        except Exception as e:
            print(f"❌ ElevenLabs audio generation failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error details: {str(e)}")
            
            # Additional debugging
            try:
                from elevenlabs import ElevenLabs
                print("✅ ElevenLabs SDK import successful")
            except ImportError as import_e:
                print(f"❌ ElevenLabs SDK import failed: {import_e}")
                print("   Try: pip install elevenlabs")
            
            if self.job_id:
                logger.log_job_error(self.job_id, str(e), "ELEVENLABS_AUDIO_TEST")
            
            self.test_results["elevenlabs_audio"] = False
            return None
    
    def test_single_video_generation(self):
        """Test generating a single video clip."""
        print("\n🎬 Testing Single Video Generation...")
        print("=" * 50)
        
        try:
            # Ensure we have analysis data
            if not self.ensure_transcript_analysis():
                print("❌ Cannot generate video without transcript analysis")
                self.test_results["single_video"] = False
                return []
            
            # Generate tailored key phrases and use the first one
            key_phrases = extract_key_phrases(
                SAMPLE_TRANSCRIPT, self.sentiment_data, num_phrases=1,
                gender=SAMPLE_GENDER, age_group=SAMPLE_AGE_GROUP, visual_style=SAMPLE_VISUAL_STYLE
            )
            test_prompt = key_phrases[0]
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
            # Ensure we have analysis data
            if not self.ensure_transcript_analysis():
                print("❌ Cannot generate videos without transcript analysis")
                self.test_results["multiple_video"] = False
                return []
            
            # Generate tailored key phrases (limit to 2 for testing)
            test_phrases = extract_key_phrases(
                SAMPLE_TRANSCRIPT, self.sentiment_data, num_phrases=2,
                gender=SAMPLE_GENDER, age_group=SAMPLE_AGE_GROUP, visual_style=SAMPLE_VISUAL_STYLE
            )
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
    
    def test_video_duration(self, video_file_path):
        """Test video duration detection with all available methods."""
        print("\n⏱️ Testing Video Duration Detection...")
        print("=" * 50)
        
        if not os.path.exists(video_file_path):
            print(f"❌ Video file not found: {video_file_path}")
            self.test_results["video_duration"] = False
            return None
        
        print(f"🎬 Testing video: {video_file_path}")
        print(f"📁 File exists: {os.path.exists(video_file_path)}")
        file_size = os.path.getsize(video_file_path) / (1024*1024)  # MB
        print(f"📏 File size: {file_size:.2f} MB")
        print()
        
        # Check library availability
        print("🔍 Available Methods:")
        print(f"   - OpenCV: {'✅ Available' if HAS_OPENCV else '❌ Not available'}")
        print(f"   - MoviePy: {'✅ Available' if HAS_MOVIEPY else '❌ Not available'}")
        print(f"   - FFmpeg: {'✅ Available' if HAS_FFMPEG else '❌ Not available'}")
        print(f"   - Available methods: {get_available_methods()}")
        print()
        
        results = {}
        successful_methods = 0
        
        # Test OpenCV method
        if HAS_OPENCV:
            print("🔧 Testing OpenCV method...")
            try:
                opencv_duration = get_video_duration_opencv(video_file_path)
                results['opencv'] = opencv_duration
                if opencv_duration is not None:
                    print(f"   ✅ OpenCV: {opencv_duration:.3f}s ({format_duration(opencv_duration)})")
                    successful_methods += 1
                else:
                    print("   ❌ OpenCV: Failed")
            except Exception as e:
                print(f"   ❌ OpenCV: Error - {e}")
                results['opencv'] = None
        else:
            print("   ⏭️ OpenCV: Skipped (not available)")
        
        # Test MoviePy method
        if HAS_MOVIEPY:
            print("🔧 Testing MoviePy method...")
            try:
                moviepy_duration = get_video_duration_moviepy(video_file_path)
                results['moviepy'] = moviepy_duration
                if moviepy_duration is not None:
                    print(f"   ✅ MoviePy: {moviepy_duration:.3f}s ({format_duration(moviepy_duration)})")
                    successful_methods += 1
                else:
                    print("   ❌ MoviePy: Failed")
            except Exception as e:
                print(f"   ❌ MoviePy: Error - {e}")
                results['moviepy'] = None
        else:
            print("   ⏭️ MoviePy: Skipped (not available)")
        
        # Test FFmpeg method
        if HAS_FFMPEG:
            print("🔧 Testing FFmpeg method...")
            try:
                ffmpeg_duration = get_video_duration_ffmpeg(video_file_path)
                results['ffmpeg'] = ffmpeg_duration
                if ffmpeg_duration is not None:
                    print(f"   ✅ FFmpeg: {ffmpeg_duration:.3f}s ({format_duration(ffmpeg_duration)})")
                    successful_methods += 1
                else:
                    print("   ❌ FFmpeg: Failed")
            except Exception as e:
                print(f"   ❌ FFmpeg: Error - {e}")
                results['ffmpeg'] = None
        else:
            print("   ⏭️ FFmpeg: Skipped (not available)")
        
        print()
        
        # Test auto method (unified)
        print("🔧 Testing unified auto method...")
        try:
            auto_duration = get_video_duration(video_file_path, "auto")
            if auto_duration is not None:
                print(f"   ✅ Auto: {auto_duration:.3f}s ({format_duration(auto_duration)})")
            else:
                print("   ❌ Auto: Failed")
        except Exception as e:
            print(f"   ❌ Auto: Error - {e}")
            auto_duration = None
        
        print()
        
        # Compare results
        successful_results = {k: v for k, v in results.items() if v is not None}
        
        if successful_results:
            print("📊 Results Comparison:")
            durations = list(successful_results.values())
            avg_duration = sum(durations) / len(durations)
            
            for method, duration in successful_results.items():
                diff = abs(duration - avg_duration)
                diff_percent = (diff / avg_duration) * 100 if avg_duration > 0 else 0
                status = "⚠️" if diff_percent > 1.0 else "✅"
                print(f"   {status} {method.capitalize()}: {duration:.3f}s (±{diff:.3f}s, {diff_percent:.1f}%)")
            
            print(f"   📈 Average: {avg_duration:.3f}s")
            print(f"   📏 Max difference: {max(durations) - min(durations):.3f}s")
            
            if max(durations) - min(durations) > 0.5:
                print("   ⚠️ Warning: Large differences detected between methods")
            else:
                print("   ✅ All methods agree within acceptable tolerance")
            
            # Log duration for pipeline use
            if self.job_id:
                logger.log_step(self.job_id, "VIDEO_DURATION", f"Video duration: {avg_duration:.3f}s (detected by {list(successful_results.keys())})")
            
            self.test_results["video_duration"] = True
            return avg_duration
        else:
            print("❌ No methods succeeded!")
            self.test_results["video_duration"] = False
            return None
        
        print("\n" + "="*60)
    
    def test_standalone_video_stitching(self):
        """Test standalone video stitching with user-provided video files."""
        print("\n🎞️ Testing Standalone Video Stitching...")
        print("=" * 50)
        
        video_paths = []
        
        # Ask for first video file
        video_file_1 = input("Enter path to first video file: ").strip()
        if video_file_1:
            # Remove quotes if present
            if video_file_1.startswith('"') and video_file_1.endswith('"'):
                video_file_1 = video_file_1[1:-1]
            elif video_file_1.startswith("'") and video_file_1.endswith("'"):
                video_file_1 = video_file_1[1:-1]
            video_paths.append(video_file_1)
        
        # Ask for second video file
        video_file_2 = input("Enter path to second video file: ").strip()
        if video_file_2:
            # Remove quotes if present
            if video_file_2.startswith('"') and video_file_2.endswith('"'):
                video_file_2 = video_file_2[1:-1]
            elif video_file_2.startswith("'") and video_file_2.endswith("'"):
                video_file_2 = video_file_2[1:-1]
            video_paths.append(video_file_2)
        
        if len(video_paths) < 1:
            print("❌ No video files provided")
            self.test_results["standalone_video_stitching"] = False
            return None
        
        if len(video_paths) == 1:
            print("⚠️  Only one video file provided, will copy it to output")
        
        try:
            print(f"\n📋 Video files to stitch:")
            for i, path in enumerate(video_paths, 1):
                print(f"   {i}. {path}")
            
            # Use the standalone video stitcher
            output_path = stitch_videos(video_paths)
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"\n✅ Standalone video stitching completed successfully!")
                print(f"📁 Output file: {output_path}")
                print(f"📏 File size: {file_size / (1024*1024):.2f} MB")
                
                # Test video duration of output
                try:
                    duration = get_video_duration(output_path)
                    if duration:
                        print(f"⏱️  Output duration: {duration:.3f} seconds ({format_duration(duration)})")
                except Exception as e:
                    print(f"⚠️  Could not get output duration: {e}")
                
                self.test_results["standalone_video_stitching"] = True
                return output_path
            else:
                print(f"❌ Output video not found: {output_path}")
                self.test_results["standalone_video_stitching"] = False
                return None
                
        except Exception as e:
            print(f"❌ Standalone video stitching failed: {e}")
            self.test_results["standalone_video_stitching"] = False
            return None
    
    def test_full_pipeline_with_sample_data(self):
        """Test the full pipeline using sample data with dynamic GCP NLP analysis."""
        print("\n🚀 Testing Full Pipeline with Sample Data...")
        print("=" * 50)
        
        # Step 1: Analyze sample transcript with GCP NLP
        if not self.test_transcript_analysis():
            return False
        
        # Step 2: Generate audio
        audio_path = self.test_audio_generation()
        if not audio_path:
            return False
        
        # Step 3: Generate videos (limited to 2 for testing)
        # Use dynamically generated key phrases for video generation
        key_phrases = extract_key_phrases(
            SAMPLE_TRANSCRIPT, self.sentiment_data, num_phrases=2,
            gender=SAMPLE_GENDER, age_group=SAMPLE_AGE_GROUP, visual_style=SAMPLE_VISUAL_STYLE
        )
        video_paths = generate_videos_from_phrases(key_phrases, self.job_id)
        if not video_paths:
            return False
        
        # Step 4: Stitch everything together
        final_video = self.test_video_stitching(video_paths, audio_path)
        if not final_video:
            return False
        
        print("\n🎉 Full pipeline test completed successfully!")
        print(f"📊 Analysis Results:")
        print(f"   Sentiment: {self.sentiment_data.get('sentiment', 'unknown')}")
        print(f"   Topics: {self.sentiment_data.get('topics', [])}")
        print(f"   User Attributes: gender={SAMPLE_GENDER}, age_group={SAMPLE_AGE_GROUP}, visual_style={SAMPLE_VISUAL_STYLE}")
        logger.log_job_complete(self.job_id, final_video, len(video_paths), len(key_phrases))
        return True
    
    def test_stylized_pipeline(self, style="Studio Ghibli"):
        """Test the stylized pipeline: OpenAI image + FAL image-to-video, with input checks after each step."""
        print(f"\n🖼️🎬 Testing Stylized Pipeline ({style})...")
        print("=" * 50)
        try:
            # Ensure we have analysis data
            if not self.ensure_transcript_analysis():
                print("❌ Cannot generate stylized content without transcript analysis")
                self.test_results[f"stylized_{style}"] = False
                return []
            
            key_phrases = extract_key_phrases(
                SAMPLE_TRANSCRIPT, self.sentiment_data, num_phrases=2,
                gender=SAMPLE_GENDER, age_group=SAMPLE_AGE_GROUP, visual_style=style
            )
            video_paths = []
            for i, phrase in enumerate(key_phrases):
                image_path = logger.get_job_file_path(self.job_id, f"openai_image_{i}.png")
                generate_image_with_openai(phrase, image_path)
                print(f"✅ Image {i+1} generated: {image_path}")
                # Ask to move to uploading
                move_to_upload = input(f"Do you want to upload image {i+1}? (y/n): ").strip().lower()
                if move_to_upload != 'y':
                    print(f"Skipping upload for image {i+1} and image-to-video generation.")
                    continue
                # Upload image
                try:
                    upload_url = upload_image(image_path)
                    print(f"✅ Image {i+1} uploaded. URL: {upload_url}")
                except Exception as e:
                    print(f"❌ Upload failed for image {i+1}: {e}")
                    continue
                # Ask to generate image-to-video
                gen_video = input(f"Generate image-to-video for image {i+1}? (y/n): ").strip().lower()
                if gen_video != 'y':
                    print(f"Skipping image-to-video for image {i+1}.")
                    continue
                video_path = generate_video_from_image(image_path, phrase, i, self.job_id)
                video_paths.append(video_path)
            
            print(f"✅ Stylized pipeline generated {len(video_paths)} videos.")
            for path in video_paths:
                print(f"   {path} ({os.path.exists(path)})")
            
            # NEW: Extended pipeline functionality
            if len(video_paths) >= 2:
                print("\n🎞️ Extending pipeline: Stitching videos together...")
                
                # Step 1: Stitch videos together
                stitched_video_path = logger.get_job_file_path(self.job_id, "stitched_video.mp4")
                try:
                    final_stitched_path = stitch_videos(video_paths, stitched_video_path)
                    print(f"✅ Videos stitched successfully: {final_stitched_path}")
                    
                    # Step 2: Get video duration
                    video_duration = get_video_duration(final_stitched_path)
                    if video_duration:
                        print(f"✅ Stitched video duration: {video_duration:.2f} seconds")
                        
                        # Step 3: Generate text that matches video length using OpenAI GPT-4o
                        generated_text = generate_text_for_video_length(
                            video_duration, 
                            SAMPLE_TRANSCRIPT, 
                            self.job_id,
                            key_phrases
                        )
                        
                        if generated_text:
                            # Save generated text to file
                            text_file_path = logger.get_job_file_path(self.job_id, "generated_text.txt")
                            with open(text_file_path, "w", encoding="utf-8") as f:
                                f.write(generated_text)
                            
                            print(f"✅ Generated text saved to: {text_file_path}")
                            print(f"📝 Text preview: {generated_text[:150]}...")
                            
                            # Step 4: Generate audio narration using ElevenLabs
                            print("\n🎵 Generating audio narration with ElevenLabs...")
                            try:
                                audio_path = generate_voice(generated_text, self.job_id, gender=SAMPLE_GENDER)
                                
                                if audio_path and os.path.exists(audio_path):
                                    audio_file_size = os.path.getsize(audio_path)
                                    print(f"✅ Audio narration generated: {audio_path}")
                                    print(f"📏 Audio file size: {audio_file_size / 1024:.2f} KB")
                                    
                                    # Try to get audio duration if possible
                                    try:
                                        import subprocess
                                        # Use ffprobe to get audio duration (works with MP3)
                                        ffprobe_cmd = [
                                            "ffprobe",
                                            "-v", "quiet",
                                            "-show_entries", "format=duration",
                                            "-of", "default=noprint_wrappers=1:nokey=1",
                                            audio_path
                                        ]
                                        
                                        result = subprocess.run(
                                            ffprobe_cmd, 
                                            capture_output=True, 
                                            text=True, 
                                            timeout=10,
                                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                                        )
                                        
                                        if result.returncode == 0 and result.stdout.strip():
                                            audio_duration = float(result.stdout.strip())
                                            print(f"🎵 Audio duration: {audio_duration:.2f} seconds")
                                            
                                            # Compare with video duration
                                            duration_diff = abs(audio_duration - video_duration)
                                            print(f"⏱️ Duration comparison:")
                                            print(f"   Video: {video_duration:.2f}s")
                                            print(f"   Audio: {audio_duration:.2f}s")
                                            print(f"   Difference: {duration_diff:.2f}s")
                                            
                                            if duration_diff <= 2.0:  # Within 2 seconds is good
                                                print("✅ Audio and video durations are well matched!")
                                            else:
                                                print("⚠️ Audio and video durations differ significantly")
                                        else:
                                            print("⚠️ Could not determine audio duration using ffprobe")
                                                
                                    except Exception as e:
                                        print(f"⚠️ Could not analyze audio duration: {e}")
                                    
                                    # Store audio generation results
                                    self.test_results[f"stylized_{style}_audio_generation"] = True
                                    
                                    # Save audio path for potential future use
                                    audio_info_path = logger.get_job_file_path(self.job_id, "audio_info.txt")
                                    with open(audio_info_path, "w", encoding="utf-8") as f:
                                        f.write(f"Audio file: {audio_path}\n")
                                        f.write(f"Generated from text: {generated_text[:100]}...\n")
                                        f.write(f"Target video duration: {video_duration:.2f}s\n")
                                    
                                    # Step 5: Combine video and audio into final narrated video
                                    print("\n🎬 Creating final video with audio narration...")
                                    try:
                                        final_video_path = logger.get_job_file_path(self.job_id, "final_narrated_video.mp4")
                                        combined_video_path = add_audio_to_video(
                                            final_stitched_path, 
                                            audio_path, 
                                            final_video_path
                                        )
                                        
                                        if combined_video_path and os.path.exists(combined_video_path):
                                            final_file_size = os.path.getsize(combined_video_path)
                                            print(f"✅ Final narrated video created successfully!")
                                            print(f"   Video file: {combined_video_path}")
                                            print(f"   File size: {final_file_size / (1024*1024):.2f} MB")
                                            
                                            # Get final video duration to verify
                                            try:
                                                final_duration = get_video_duration(combined_video_path)
                                                if final_duration:
                                                    print(f"   Final duration: {final_duration:.2f} seconds")
                                                    print(f"   Duration difference from original: {abs(final_duration - video_duration):.2f}s")
                                            except Exception as e:
                                                print(f"   Could not verify final duration: {e}")
                                            
                                            # Store final video combination results
                                            self.test_results[f"stylized_{style}_final_video"] = True
                                            
                                        else:
                                            print("❌ Failed to create final narrated video")
                                            self.test_results[f"stylized_{style}_final_video"] = False
                                    
                                    except Exception as e:
                                        print(f"❌ Video+audio combination failed: {e}")
                                        self.test_results[f"stylized_{style}_final_video"] = False
                                else:
                                    print("❌ Audio generation failed - file not created")
                                    self.test_results[f"stylized_{style}_audio_generation"] = False
                                    self.test_results[f"stylized_{style}_final_video"] = False
                            except Exception as e:
                                print(f"❌ Audio generation failed: {e}")
                                self.test_results[f"stylized_{style}_audio_generation"] = False
                                self.test_results[f"stylized_{style}_final_video"] = False
                        else:
                            self.test_results[f"stylized_{style}_text_generation"] = False
                            self.test_results[f"stylized_{style}_audio_generation"] = False
                            self.test_results[f"stylized_{style}_final_video"] = False
                    else:
                        print("❌ Failed to detect video duration")
                        self.test_results[f"stylized_{style}_duration"] = False
                        self.test_results[f"stylized_{style}_text_generation"] = False
                        self.test_results[f"stylized_{style}_audio_generation"] = False
                        self.test_results[f"stylized_{style}_final_video"] = False
                        
                except Exception as e:
                    print(f"❌ Video stitching failed: {e}")
                    self.test_results[f"stylized_{style}_stitching"] = False
                    self.test_results[f"stylized_{style}_duration"] = False
                    self.test_results[f"stylized_{style}_text_generation"] = False
                    self.test_results[f"stylized_{style}_audio_generation"] = False
                    self.test_results[f"stylized_{style}_final_video"] = False
            else:
                print(f"⚠️ Only {len(video_paths)} video(s) generated, skipping stitching (need at least 2)")
                self.test_results[f"stylized_{style}_stitching"] = False
                self.test_results[f"stylized_{style}_duration"] = False
                self.test_results[f"stylized_{style}_text_generation"] = False
                self.test_results[f"stylized_{style}_audio_generation"] = False
                self.test_results[f"stylized_{style}_final_video"] = False
            
            self.test_results[f"stylized_{style}"] = all(os.path.exists(p) for p in video_paths)
            return video_paths
        except Exception as e:
            print(f"❌ Stylized pipeline failed: {e}")
            self.test_results[f"stylized_{style}"] = False
            return []

    def test_blog_avatar_pipeline(self, style="Blog (Female)"):
        """Test the blog avatar video pipeline."""
        print(f"\n🧑‍💼🎬 Testing Blog Avatar Pipeline ({style})...")
        print("=" * 50)
        try:
            avatar_id = "any_female_primary" if style == "Blog (Female)" else "any_male_primary"
            # Use the raw transcript as the script for a natural story narration
            script = SAMPLE_TRANSCRIPT.strip()
            video_path = generate_blog_avatar_video(script, avatar_id, 0, self.job_id)
            print(f"✅ Blog avatar video generated: {video_path} ({os.path.exists(video_path)})")
            self.test_results[f"blog_avatar_{style}"] = os.path.exists(video_path)
            return [video_path]
        except Exception as e:
            print(f"❌ Blog avatar pipeline failed: {e}")
            self.test_results[f"blog_avatar_{style}"] = False
            return []

    def test_text_to_blog_pipeline(self, gender="female"):
        """Test the new text-to-blog pipeline that generates 25-second coherent dialog."""
        print(f"\n📝🎬 Testing Text-to-Blog Pipeline ({gender})...")
        print("=" * 50)
        try:
            # Step 1: Generate 25-second coherent dialog from sample text (third-person)
            test_name = "Jill" if gender.lower() == "female" else "John"
            print(f"🤖 Generating 25-second coherent third-person dialog about {test_name}...")
            dialog = generate_text_for_video_length(25.0, SAMPLE_TRANSCRIPT, self.job_id, third_person=True, person_name=test_name)
            
            if not dialog:
                dialog = SAMPLE_TRANSCRIPT  # Fallback
                print("⚠️  Using original text as fallback for dialog")
            
            print(f"✅ Generated third-person dialog about {test_name} ({len(dialog.split())} words): {dialog[:100]}...")
            
            # Step 2: Determine avatar ID based on gender
            avatar_id = "any_female_primary" if gender.lower() == "female" else "any_male_primary"
            print(f"🧑‍💼 Using avatar: {avatar_id}")
            
            # Step 3: Generate talking avatar video (includes audio automatically)
            print("🎬 Generating talking avatar video with built-in audio...")
            print("   Note: veed/avatars/text-to-video generates both video and audio automatically")
            video_path = generate_blog_avatar_video(dialog, avatar_id, 0, self.job_id)
            
            success = os.path.exists(video_path)
            print(f"✅ Text-to-blog video generated: {video_path} (exists: {success})")
            
            if success:
                # Get file size info
                file_size = os.path.getsize(video_path)
                print(f"   File size: {file_size / (1024*1024):.2f} MB")
                print(f"   Narration: Third-person about {test_name}")
                
                # Try to get video duration
                try:
                    from video_utils import get_video_duration
                    duration = get_video_duration(video_path)
                    if duration:
                        print(f"   Video duration: {duration:.2f} seconds")
                        if abs(duration - 25.0) <= 3.0:  # Within 3 seconds is reasonable
                            print("   ✅ Duration matches target (25 seconds)")
                        else:
                            print(f"   ⚠️  Duration differs from target by {abs(duration - 25.0):.1f} seconds")
                except Exception as e:
                    print(f"   ⚠️  Could not detect duration: {e}")
            
            self.test_results[f"text_to_blog_{gender}"] = success
            return [video_path] if success else []
            
        except Exception as e:
            print(f"❌ Text-to-blog pipeline failed: {e}")
            self.test_results[f"text_to_blog_{gender}"] = False
            return []

    def test_veo2_image_to_video(self):
        """Test the new VEO2 image-to-video functionality."""
        print("\n🎬🖼️ Testing VEO2 Image-to-Video Generation...")
        print("=" * 50)
        try:
            # First, we need an image to work with
            image_path = "test_piwigo_image.png"
            
            # Create a test image if it doesn't exist
            if not os.path.exists(image_path):
                from PIL import Image
                img = Image.new('RGB', (512, 512), color='red')
                img.save(image_path)
                print(f"Created test image: {image_path}")
            
            # Test prompt for the image-to-video generation
            test_prompt = "A lego chef cooking eggs"
            
            print(f"📸 Using image: {image_path}")
            print(f"📝 Using prompt: {test_prompt}")
            
            # Generate video from image using VEO2 model
            video_path = generate_video_from_image(image_path, test_prompt, 0, self.job_id)
            
            success = os.path.exists(video_path)
            print(f"✅ VEO2 image-to-video generated: {video_path} (exists: {success})")
            
            self.test_results["veo2_image_to_video"] = success
            return [video_path] if success else []
            
        except Exception as e:
            print(f"❌ VEO2 image-to-video test failed: {e}")
            self.test_results["veo2_image_to_video"] = False
            return []
    
    def test_piwigo_upload(self, image_path=None):
        """Test uploading an image to Piwigo and print the result."""
        print("\n🖼️ Testing Piwigo Image Upload...")
        print("=" * 50)
        try:
            # Use provided image or create a dummy one
            if image_path is None:
                image_path = "test_piwigo_image.png"
                # Create a small dummy image if it doesn't exist
                if not os.path.exists(image_path):
                    from PIL import Image
                    img = Image.new('RGB', (64, 64), color = 'blue')
                    img.save(image_path)
                    print(f"Created dummy image: {image_path}")
            url = upload_image(image_path)
            print(f"✅ Piwigo upload successful! Public URL: {url}")
            self.test_results["piwigo_upload"] = True
            return url
        except Exception as e:
            print(f"❌ Piwigo upload failed: {e}")
            self.test_results["piwigo_upload"] = False
            return None
    
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

    def test_comprehensive_pipeline(self):
        """Test the complete pipeline with user-selected prompts, style, gender, and age."""
        print("\n🚀 Testing Comprehensive End-to-End Pipeline...")
        print("=" * 50)
        
        # Step 1: Choose test prompt
        test_prompts = [
            {
                "name": "Morning Adventure",
                "text": """This morning started with the most incredible sunrise I've ever seen. The sky was painted in brilliant oranges and pinks as I stepped outside for my morning walk. The air was crisp and fresh, filled with the sounds of birds singing their morning songs. I walked through the local park where early joggers were already out, and the dew on the grass sparkled like tiny diamonds. I stopped by my favorite coffee shop where Maria, the owner, greeted me with her usual warm smile and made my perfect cappuccino. The day felt full of possibilities and new adventures waiting to unfold."""
            },
            {
                "name": "Creative Breakthrough",
                "text": """Today was the day I finally finished my art project that I've been working on for months. Standing back and looking at the completed painting, I felt this incredible sense of accomplishment wash over me. The colors blended perfectly - deep blues flowing into warm yellows, creating exactly the mood I had envisioned. My studio was a mess of paint tubes and brushes, but it felt like a beautiful chaos of creativity. I called my best friend to share the news, and we celebrated with takeout pizza and wine while discussing my next artistic adventure."""
            },
            {
                "name": "Family Gathering",
                "text": """The family reunion today was absolutely wonderful. Three generations gathered in my grandmother's backyard, the same place where we've been meeting for family celebrations for over twenty years. The kids ran around playing tag while the adults shared stories and laughter around the picnic table. Grandma's famous apple pie was the star of the dessert table, and Uncle Joe entertained everyone with his guitar playing just like he used to when I was little. These moments remind me how precious family connections are and how they anchor us through all of life's changes."""
            },
            {
                "name": "Learning Journey",
                "text": """I started learning a new language today, and it feels like opening a door to an entirely new world. The first lesson was challenging but exciting - rolling Spanish words around in my mouth, trying to master the pronunciation. I practiced with a language app during my lunch break, then watched a Spanish movie with subtitles in the evening. Each new word I learned felt like a small victory. I'm planning to visit Barcelona next year, and I can already imagine myself ordering coffee in Spanish and chatting with locals about their beautiful city."""
            },
            {
                "name": "Nature Discovery",
                "text": """I spent the entire day hiking through the forest preserve, discovering hidden trails I'd never explored before. The autumn leaves created a golden canopy above me, and every step brought new sights and sounds. I found a small creek where I sat on a moss-covered rock and just listened to the water flowing over stones. A family of deer appeared across the stream, watching me curiously before gracefully bounding away. I collected a few perfect fallen leaves and interesting stones, natural treasures that will remind me of this peaceful, restorative day in nature."""
            }
        ]
        
        print("\n📝 Choose a test prompt:")
        for i, prompt in enumerate(test_prompts, 1):
            print(f"{i}. {prompt['name']}")
            print(f"   Preview: {prompt['text'][:100]}...")
            print()
        
        while True:
            choice = input(f"Enter your choice (1-{len(test_prompts)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(test_prompts):
                selected_prompt = test_prompts[int(choice) - 1]
                break
            print("❌ Invalid choice. Please try again.")
        
        print(f"\n✅ Selected: {selected_prompt['name']}")
        print(f"Full text: {selected_prompt['text']}")
        
        # Step 2: Choose style
        style_key = select_style_menu(STYLE_OPTIONS, "Select visual style:")
        style_map = {
            "ghibli": "Studio Ghibli",
            "pixar": "Pixar", 
            "anime": "Anime",
            "watercolor": "Watercolor",
            "cyberpunk": "Cyberpunk",
            "realistic": "Realistic"
        }
        selected_style = style_map[style_key]
        
        # Step 3: Choose gender
        print("\nSelect gender:")
        print("1. Female")
        print("2. Male")
        while True:
            gender_choice = input("Enter your choice (1-2): ").strip()
            if gender_choice == "1":
                selected_gender = "female"
                break
            elif gender_choice == "2":
                selected_gender = "male"
                break
            print("❌ Invalid choice. Please try again.")
        
        # Step 4: Choose age group
        age_groups = ["18-25", "26-35", "36-45", "46-55", "55+"]
        print("\nSelect age group:")
        for i, age in enumerate(age_groups, 1):
            print(f"{i}. {age}")
        while True:
            age_choice = input(f"Enter your choice (1-{len(age_groups)}): ").strip()
            if age_choice.isdigit() and 1 <= int(age_choice) <= len(age_groups):
                selected_age = age_groups[int(age_choice) - 1]
                break
            print("❌ Invalid choice. Please try again.")
        
        print(f"\n🎬 Pipeline Configuration:")
        print(f"   Prompt: {selected_prompt['name']}")
        print(f"   Style: {selected_style}")
        print(f"   Gender: {selected_gender}")
        print(f"   Age: {selected_age}")
        print()
        
        input("Press Enter to start the comprehensive pipeline...")
        
        try:
            # Override sample data with user selections
            original_transcript = SAMPLE_TRANSCRIPT
            original_gender = SAMPLE_GENDER
            original_age = SAMPLE_AGE_GROUP
            original_style = SAMPLE_VISUAL_STYLE
            
            # Temporarily replace globals (not ideal but works for testing)
            globals()['SAMPLE_TRANSCRIPT'] = selected_prompt['text']
            globals()['SAMPLE_GENDER'] = selected_gender
            globals()['SAMPLE_AGE_GROUP'] = selected_age
            globals()['SAMPLE_VISUAL_STYLE'] = selected_style
            
            # Step 5: Run transcript analysis
            print("\n🔍 STEP 1: Analyzing transcript with GCP NLP...")
            if not self.test_transcript_analysis():
                print("❌ Pipeline failed at transcript analysis")
                return False
            
            # Step 6: Extract key phrases dynamically (up to 5 based on content importance)
            print("\n🖼️ STEP 2: Analyzing content and generating key phrases...")
            print("🤖 AI is determining the optimal number of scenes (up to 5) based on content importance...")
            
            key_phrases = extract_key_phrases(
                selected_prompt['text'], self.sentiment_data, num_phrases=5,
                gender=selected_gender, age_group=selected_age, visual_style=selected_style
            )
            
            print(f"✅ Generated {len(key_phrases)} key phrases:")
            for i, phrase in enumerate(key_phrases, 1):
                print(f"   {i}. {phrase[:80]}...")
            print()
            
            video_paths = []
            for i, phrase in enumerate(key_phrases):
                print(f"\n📸 Generating image {i+1}/{len(key_phrases)}...")
                image_path = logger.get_job_file_path(self.job_id, f"openai_image_{i}.png")
                generate_image_with_openai(phrase, image_path)
                print(f"✅ Image {i+1} generated: {image_path}")
                
                print(f"📤 Uploading image {i+1}...")
                try:
                    upload_url = upload_image(image_path)
                    print(f"✅ Image {i+1} uploaded: {upload_url}")
                except Exception as e:
                    print(f"❌ Upload failed for image {i+1}: {e}")
                    continue
                
                print(f"🎬 Generating video {i+1}/{len(key_phrases)}...")
                video_path = generate_video_from_image(image_path, phrase, i, self.job_id)
                video_paths.append(video_path)
                print(f"✅ Video {i+1} generated: {video_path}")
            
            if len(video_paths) < 2:
                print("❌ Pipeline failed: Need at least 2 videos for stitching")
                return False
            
            print(f"\n✅ Successfully generated {len(video_paths)}/{len(key_phrases)} videos")
            
            # Step 7: Stitch videos
            print(f"\n🎞️ STEP 3: Stitching {len(video_paths)} videos together...")
            stitched_video_path = logger.get_job_file_path(self.job_id, "stitched_video.mp4")
            final_stitched_path = stitch_videos(video_paths, stitched_video_path)
            print(f"✅ Videos stitched: {final_stitched_path}")
            
            # Step 8: Get video duration
            print("\n⏱️ STEP 4: Detecting video duration...")
            video_duration = get_video_duration(final_stitched_path)
            if not video_duration:
                print("❌ Pipeline failed: Could not detect video duration")
                return False
            print(f"✅ Video duration: {video_duration:.2f} seconds")
            
            # Step 9: Generate matching text
            print("\n🤖 STEP 5: Generating text with OpenAI GPT-4o...")
            generated_text = generate_text_for_video_length(
                video_duration, 
                selected_prompt['text'], 
                self.job_id,
                key_phrases
            )
            if not generated_text:
                print("❌ Pipeline failed: Could not generate text")
                return False
            
            text_file_path = logger.get_job_file_path(self.job_id, "generated_text.txt")
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(generated_text)
            print(f"✅ Text generated and saved: {text_file_path}")
            
            # Step 10: Generate audio
            print("\n🎵 STEP 6: Generating audio with ElevenLabs...")
            audio_path = generate_voice(generated_text, self.job_id, gender=selected_gender)
            if not audio_path or not os.path.exists(audio_path):
                print("❌ Pipeline failed: Could not generate audio")
                return False
            print(f"✅ Audio generated: {audio_path}")
            
            # Step 11: Create final video with audio
            print("\n🎬 STEP 7: Creating final narrated video...")
            final_video_path = logger.get_job_file_path(self.job_id, "final_narrated_video.mp4")
            combined_video_path = add_audio_to_video(
                final_stitched_path, 
                audio_path, 
                final_video_path
            )
            
            if not combined_video_path or not os.path.exists(combined_video_path):
                print("❌ Pipeline failed: Could not create final video")
                return False
            
            final_file_size = os.path.getsize(combined_video_path)
            print(f"✅ Final narrated video created: {combined_video_path}")
            print(f"   File size: {final_file_size / (1024*1024):.2f} MB")
            
            # Step 12: Create comprehensive summary
            summary_path = logger.get_job_file_path(self.job_id, "comprehensive_pipeline_summary.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write("=== COMPREHENSIVE PIPELINE SUMMARY ===\n\n")
                f.write(f"Prompt: {selected_prompt['name']}\n")
                f.write(f"Style: {selected_style}\n")
                f.write(f"Gender: {selected_gender}\n")
                f.write(f"Age Group: {selected_age}\n")
                f.write(f"Key Phrases Generated: {len(key_phrases)}\n")
                f.write(f"Videos Created: {len(video_paths)}\n")
                f.write(f"Video Duration: {video_duration:.2f} seconds\n")
                f.write(f"Generated Text Length: {len(generated_text.split())} words\n")
                f.write(f"Final Video Size: {final_file_size / (1024*1024):.2f} MB\n\n")
                f.write("=== AI-GENERATED KEY PHRASES ===\n")
                for i, phrase in enumerate(key_phrases, 1):
                    f.write(f"{i}. {phrase}\n")
                f.write("\n=== FILES CREATED ===\n")
                for i, video_path in enumerate(video_paths, 1):
                    f.write(f"Video {i}: {video_path}\n")
                f.write(f"Stitched Video: {final_stitched_path}\n")
                f.write(f"Generated Text: {text_file_path}\n")
                f.write(f"Audio Narration: {audio_path}\n")
                f.write(f"Final Narrated Video: {combined_video_path}\n\n")
                f.write("=== ORIGINAL PROMPT ===\n")
                f.write(f'"{selected_prompt["text"]}"\n\n')
                f.write("=== GENERATED NARRATION ===\n")
                f.write(f'"{generated_text}"\n')
            
            print(f"\n🎉 COMPREHENSIVE PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"📊 Generated {len(key_phrases)} key phrases → {len(video_paths)} videos → 1 final narrated video")
            print(f"📄 Full summary: {summary_path}")
            print(f"🎬 Final video: {combined_video_path}")
            
            # Restore original sample data
            globals()['SAMPLE_TRANSCRIPT'] = original_transcript
            globals()['SAMPLE_GENDER'] = original_gender  
            globals()['SAMPLE_AGE_GROUP'] = original_age
            globals()['SAMPLE_VISUAL_STYLE'] = original_style
            
            self.test_results["comprehensive_pipeline"] = True
            return True
            
        except Exception as e:
            print(f"❌ Comprehensive pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Restore original sample data
            globals()['SAMPLE_TRANSCRIPT'] = original_transcript
            globals()['SAMPLE_GENDER'] = original_gender
            globals()['SAMPLE_AGE_GROUP'] = original_age  
            globals()['SAMPLE_VISUAL_STYLE'] = original_style
            
            self.test_results["comprehensive_pipeline"] = False
            return False

    def test_async_comprehensive_pipeline(self):
        """Test the complete async pipeline with concurrent image and video generation for faster processing."""
        print("\n🚀⚡ Testing ASYNC Comprehensive End-to-End Pipeline (Concurrent Processing)...")
        print("=" * 70)
        
        # Use the same prompt selection as the regular comprehensive pipeline
        test_prompts = [
            {
                "name": "Morning Adventure",
                "text": """This morning started with the most incredible sunrise I've ever seen. The sky was painted in brilliant oranges and pinks as I stepped outside for my morning walk. The air was crisp and fresh, filled with the sounds of birds singing their morning songs. I walked through the local park where early joggers were already out, and the dew on the grass sparkled like tiny diamonds. I stopped by my favorite coffee shop where Maria, the owner, greeted me with her usual warm smile and made my perfect cappuccino. The day felt full of possibilities and new adventures waiting to unfold."""
            },
            {
                "name": "Creative Breakthrough",
                "text": """Today was the day I finally finished my art project that I've been working on for months. Standing back and looking at the completed painting, I felt this incredible sense of accomplishment wash over me. The colors blended perfectly - deep blues flowing into warm yellows, creating exactly the mood I had envisioned. My studio was a mess of paint tubes and brushes, but it felt like a beautiful chaos of creativity. I called my best friend to share the news, and we celebrated with takeout pizza and wine while discussing my next artistic adventure."""
            },
            {
                "name": "Family Gathering",
                "text": """The family reunion today was absolutely wonderful. Three generations gathered in my grandmother's backyard, the same place where we've been meeting for family celebrations for over twenty years. The kids ran around playing tag while the adults shared stories and laughter around the picnic table. Grandma's famous apple pie was the star of the dessert table, and Uncle Joe entertained everyone with his guitar playing just like he used to when I was little. These moments remind me how precious family connections are and how they anchor us through all of life's changes."""
            },
            {
                "name": "Learning Journey",
                "text": """I started learning a new language today, and it feels like opening a door to an entirely new world. The first lesson was challenging but exciting - rolling Spanish words around in my mouth, trying to master the pronunciation. I practiced with a language app during my lunch break, then watched a Spanish movie with subtitles in the evening. Each new word I learned felt like a small victory. I'm planning to visit Barcelona next year, and I can already imagine myself ordering coffee in Spanish and chatting with locals about their beautiful city."""
            },
            {
                "name": "Nature Discovery",
                "text": """I spent the entire day hiking through the forest preserve, discovering hidden trails I'd never explored before. The autumn leaves created a golden canopy above me, and every step brought new sights and sounds. I found a small creek where I sat on a moss-covered rock and just listened to the water flowing over stones. A family of deer appeared across the stream, watching me curiously before gracefully bounding away. I collected a few perfect fallen leaves and interesting stones, natural treasures that will remind me of this peaceful, restorative day in nature."""
            }
        ]
        
        print("\n📝 Choose a test prompt:")
        for i, prompt in enumerate(test_prompts, 1):
            print(f"{i}. {prompt['name']}")
            print(f"   Preview: {prompt['text'][:100]}...")
            print()
        
        while True:
            choice = input(f"Enter your choice (1-{len(test_prompts)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(test_prompts):
                selected_prompt = test_prompts[int(choice) - 1]
                break
            print("❌ Invalid choice. Please try again.")
        
        print(f"\n✅ Selected: {selected_prompt['name']}")
        print(f"Full text: {selected_prompt['text']}")
        
        # Step 2: Choose style
        style_key = select_style_menu(STYLE_OPTIONS, "Select visual style:")
        style_map = {
            "ghibli": "Studio Ghibli",
            "pixar": "Pixar", 
            "anime": "Anime",
            "watercolor": "Watercolor",
            "cyberpunk": "Cyberpunk",
            "realistic": "Realistic"
        }
        selected_style = style_map[style_key]
        
        # Step 3: Choose gender
        print("\nSelect gender:")
        print("1. Female")
        print("2. Male")
        while True:
            gender_choice = input("Enter your choice (1-2): ").strip()
            if gender_choice == "1":
                selected_gender = "female"
                break
            elif gender_choice == "2":
                selected_gender = "male"
                break
            print("❌ Invalid choice. Please try again.")
        
        # Step 4: Choose age group
        age_groups = ["18-25", "26-35", "36-45", "46-55", "55+"]
        print("\nSelect age group:")
        for i, age in enumerate(age_groups, 1):
            print(f"{i}. {age}")
        while True:
            age_choice = input(f"Enter your choice (1-{len(age_groups)}): ").strip()
            if age_choice.isdigit() and 1 <= int(age_choice) <= len(age_groups):
                selected_age = age_groups[int(age_choice) - 1]
                break
            print("❌ Invalid choice. Please try again.")
        
        print(f"\n🎬 Pipeline Configuration:")
        print(f"   Prompt: {selected_prompt['name']}")
        print(f"   Style: {selected_style}")
        print(f"   Gender: {selected_gender}")
        print(f"   Age: {selected_age}")
        print(f"   Mode: ⚡ ASYNC (Concurrent Processing)")
        print()
        
        input("Press Enter to start the ASYNC comprehensive pipeline...")
        
        # Run the async pipeline
        result = asyncio.run(self._run_async_comprehensive_pipeline(
            selected_prompt, selected_style, selected_gender, selected_age
        ))
        
        return result

    async def _run_async_comprehensive_pipeline(self, selected_prompt, selected_style, selected_gender, selected_age):
        """Internal async method to run the comprehensive pipeline with concurrent processing."""
        import time
        start_time = time.time()
        
        try:
            # Override sample data with user selections
            original_transcript = SAMPLE_TRANSCRIPT
            original_gender = SAMPLE_GENDER
            original_age = SAMPLE_AGE_GROUP
            original_style = SAMPLE_VISUAL_STYLE
            
            # Temporarily replace globals (not ideal but works for testing)
            globals()['SAMPLE_TRANSCRIPT'] = selected_prompt['text']
            globals()['SAMPLE_GENDER'] = selected_gender
            globals()['SAMPLE_AGE_GROUP'] = selected_age
            globals()['SAMPLE_VISUAL_STYLE'] = selected_style
            
            # Step 5: Run transcript analysis (still synchronous)
            print("\n🔍 STEP 1: Analyzing transcript with GCP NLP...")
            if not self.test_transcript_analysis():
                print("❌ Pipeline failed at transcript analysis")
                return False
            
            # Step 6: Extract key phrases dynamically
            print("\n🖼️ STEP 2: Analyzing content and generating key phrases...")
            print("🤖 AI is determining the optimal number of scenes (up to 5) based on content importance...")
            
            key_phrases = extract_key_phrases(
                selected_prompt['text'], self.sentiment_data, num_phrases=5,
                gender=selected_gender, age_group=selected_age, visual_style=selected_style
            )
            
            print(f"✅ Generated {len(key_phrases)} key phrases:")
            for i, phrase in enumerate(key_phrases, 1):
                print(f"   {i}. {phrase[:80]}...")
            print()
            
            # Step 7: ASYNC CONCURRENT IMAGE GENERATION
            print(f"\n📸⚡ STEP 3A: Generating {len(key_phrases)} images CONCURRENTLY...")
            image_generation_start = time.time()
            
            # Create all image generation tasks
            image_tasks = []
            image_paths = []
            for i, phrase in enumerate(key_phrases):
                image_path = logger.get_job_file_path(self.job_id, f"openai_image_{i}.png")
                image_paths.append(image_path)
                task = async_generate_image_with_openai(phrase, image_path)
                image_tasks.append(task)
            
            # Run all image generations concurrently
            print(f"🚀 Launching {len(image_tasks)} concurrent image generation tasks...")
            image_results = await asyncio.gather(*image_tasks, return_exceptions=True)
            
            image_generation_time = time.time() - image_generation_start
            
            # Check image generation results
            successful_images = []
            for i, result in enumerate(image_results):
                if isinstance(result, Exception):
                    print(f"❌ Image {i+1} failed: {result}")
                else:
                    print(f"✅ Image {i+1} generated: {result}")
                    successful_images.append((i, result, key_phrases[i]))
            
            print(f"⚡ Image generation completed in {image_generation_time:.2f} seconds")
            print(f"✅ Successfully generated {len(successful_images)}/{len(key_phrases)} images")
            
            if len(successful_images) < 2:
                print("❌ Pipeline failed: Need at least 2 images for video generation")
                return False
            
            # Step 8: ASYNC CONCURRENT VIDEO GENERATION
            print(f"\n🎬⚡ STEP 3B: Generating {len(successful_images)} videos CONCURRENTLY...")
            video_generation_start = time.time()
            
            # Upload all images first (could also be made concurrent, but limiting for now)
            print(f"📤 Uploading {len(successful_images)} images...")
            upload_tasks = []
            for i, image_path, phrase in successful_images:
                # Note: upload_image might need to be made async for true concurrency
                try:
                    upload_url = upload_image(image_path)
                    print(f"✅ Image {i+1} uploaded: {upload_url}")
                except Exception as e:
                    print(f"❌ Upload failed for image {i+1}: {e}")
                    # Remove from successful images if upload fails
                    successful_images = [(idx, path, phr) for idx, path, phr in successful_images if idx != i]
                    continue
            
            # Create all video generation tasks
            video_tasks = []
            video_paths = []
            for i, image_path, phrase in successful_images:
                task = async_generate_video_from_image(image_path, phrase, i, self.job_id)
                video_tasks.append(task)
            
            # Run all video generations concurrently
            print(f"🚀 Launching {len(video_tasks)} concurrent video generation tasks...")
            video_results = await asyncio.gather(*video_tasks, return_exceptions=True)
            
            video_generation_time = time.time() - video_generation_start
            
            # Check video generation results
            for i, result in enumerate(video_results):
                if isinstance(result, Exception):
                    print(f"❌ Video {i+1} failed: {result}")
                else:
                    print(f"✅ Video {i+1} generated: {result}")
                    video_paths.append(result)
            
            print(f"⚡ Video generation completed in {video_generation_time:.2f} seconds")
            print(f"✅ Successfully generated {len(video_paths)}/{len(successful_images)} videos")
            
            if len(video_paths) < 2:
                print("❌ Pipeline failed: Need at least 2 videos for stitching")
                return False
            
            total_generation_time = image_generation_time + video_generation_time
            print(f"\n📊 CONCURRENT GENERATION STATS:")
            print(f"   Images: {image_generation_time:.2f}s for {len(successful_images)} images ({image_generation_time/len(successful_images):.2f}s avg)")
            print(f"   Videos: {video_generation_time:.2f}s for {len(video_paths)} videos ({video_generation_time/len(video_paths):.2f}s avg)")
            print(f"   Total: {total_generation_time:.2f}s (vs ~{(len(successful_images) * 15 + len(video_paths) * 45):.0f}s estimated sequential)")
            
            # Continue with synchronous steps...
            print(f"\n🎞️ STEP 4: Stitching {len(video_paths)} videos together...")
            stitched_video_path = logger.get_job_file_path(self.job_id, "stitched_video.mp4")
            final_stitched_path = stitch_videos(video_paths, stitched_video_path)
            print(f"✅ Videos stitched: {final_stitched_path}")
            
            # Step 8: Get video duration
            print("\n⏱️ STEP 5: Detecting video duration...")
            video_duration = get_video_duration(final_stitched_path)
            if not video_duration:
                print("❌ Pipeline failed: Could not detect video duration")
                return False
            print(f"✅ Video duration: {video_duration:.2f} seconds")
            
            # Step 9: Generate matching text
            print("\n🤖 STEP 6: Generating text with OpenAI GPT-4o...")
            generated_text = generate_text_for_video_length(
                video_duration, 
                selected_prompt['text'], 
                self.job_id,
                key_phrases
            )
            if not generated_text:
                print("❌ Pipeline failed: Could not generate text")
                return False
            
            text_file_path = logger.get_job_file_path(self.job_id, "generated_text.txt")
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(generated_text)
            print(f"✅ Text generated and saved: {text_file_path}")
            
            # Step 10: Generate audio
            print("\n🎵 STEP 7: Generating audio with ElevenLabs...")
            audio_path = generate_voice(generated_text, self.job_id, gender=selected_gender)
            if not audio_path or not os.path.exists(audio_path):
                print("❌ Pipeline failed: Could not generate audio")
                return False
            print(f"✅ Audio generated: {audio_path}")
            
            # Step 11: Create final video with audio
            print("\n🎬 STEP 8: Creating final narrated video...")
            final_video_path = logger.get_job_file_path(self.job_id, "final_narrated_video.mp4")
            combined_video_path = add_audio_to_video(
                final_stitched_path, 
                audio_path, 
                final_video_path
            )
            
            if not combined_video_path or not os.path.exists(combined_video_path):
                print("❌ Pipeline failed: Could not create final video")
                return False
            
            final_file_size = os.path.getsize(combined_video_path)
            total_time = time.time() - start_time
            
            print(f"✅ Final narrated video created: {combined_video_path}")
            print(f"   File size: {final_file_size / (1024*1024):.2f} MB")
            
            # Step 12: Create comprehensive summary with timing stats
            summary_path = logger.get_job_file_path(self.job_id, "async_comprehensive_pipeline_summary.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write("=== ASYNC COMPREHENSIVE PIPELINE SUMMARY ===\n\n")
                f.write(f"Prompt: {selected_prompt['name']}\n")
                f.write(f"Style: {selected_style}\n")
                f.write(f"Gender: {selected_gender}\n")
                f.write(f"Age Group: {selected_age}\n")
                f.write(f"Processing Mode: ASYNC (Concurrent)\n")
                f.write(f"Key Phrases Generated: {len(key_phrases)}\n")
                f.write(f"Images Created: {len(successful_images)}\n")
                f.write(f"Videos Created: {len(video_paths)}\n")
                f.write(f"Video Duration: {video_duration:.2f} seconds\n")
                f.write(f"Generated Text Length: {len(generated_text.split())} words\n")
                f.write(f"Final Video Size: {final_file_size / (1024*1024):.2f} MB\n\n")
                f.write("=== PERFORMANCE METRICS ===\n")
                f.write(f"Image Generation Time: {image_generation_time:.2f}s (concurrent)\n")
                f.write(f"Video Generation Time: {video_generation_time:.2f}s (concurrent)\n")
                f.write(f"Total Generation Time: {total_generation_time:.2f}s\n")
                f.write(f"Total Pipeline Time: {total_time:.2f}s\n")
                f.write(f"Estimated Sequential Time: ~{(len(successful_images) * 15 + len(video_paths) * 45):.0f}s\n")
                f.write(f"Time Saved: ~{(len(successful_images) * 15 + len(video_paths) * 45) - total_generation_time:.0f}s\n\n")
                f.write("=== AI-GENERATED KEY PHRASES ===\n")
                for i, phrase in enumerate(key_phrases, 1):
                    f.write(f"{i}. {phrase}\n")
                f.write("\n=== FILES CREATED ===\n")
                for i, video_path in enumerate(video_paths, 1):
                    f.write(f"Video {i}: {video_path}\n")
                f.write(f"Stitched Video: {final_stitched_path}\n")
                f.write(f"Generated Text: {text_file_path}\n")
                f.write(f"Audio Narration: {audio_path}\n")
                f.write(f"Final Narrated Video: {combined_video_path}\n\n")
                f.write("=== ORIGINAL PROMPT ===\n")
                f.write(f'"{selected_prompt["text"]}"\n\n')
                f.write("=== GENERATED NARRATION ===\n")
                f.write(f'"{generated_text}"\n')
            
            print(f"\n🎉⚡ ASYNC COMPREHENSIVE PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"📊 Generated {len(key_phrases)} key phrases → {len(video_paths)} videos → 1 final narrated video")
            print(f"⚡ Time saved with concurrent processing: ~{(len(successful_images) * 15 + len(video_paths) * 45) - total_generation_time:.0f} seconds")
            print(f"📄 Full summary: {summary_path}")
            print(f"🎬 Final video: {combined_video_path}")
            
            # Restore original sample data
            globals()['SAMPLE_TRANSCRIPT'] = original_transcript
            globals()['SAMPLE_GENDER'] = original_gender  
            globals()['SAMPLE_AGE_GROUP'] = original_age
            globals()['SAMPLE_VISUAL_STYLE'] = original_style
            
            self.test_results["async_comprehensive_pipeline"] = True
            return True
            
        except Exception as e:
            print(f"❌ Async comprehensive pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            
            # Restore original sample data
            globals()['SAMPLE_TRANSCRIPT'] = original_transcript
            globals()['SAMPLE_GENDER'] = original_gender
            globals()['SAMPLE_AGE_GROUP'] = original_age  
            globals()['SAMPLE_VISUAL_STYLE'] = original_style
            
            self.test_results["async_comprehensive_pipeline"] = False
            return False

def show_menu():
    """Display the test menu."""
    print("\n🧪 Video Generation Pipeline Tester")
    print("=" * 50)
    print("1. Test Transcript Analysis with GCP NLP (dynamic sentiment & topics)")
    print("2. Test Audio Generation")
    print("3. Test Single Video Generation")
    print("4. Test Multiple Video Generation (2 clips)")
    print("5. Test Video Stitching (requires audio + videos)")
    print("6. Test Standalone Video Stitching (custom video files)")
    print("7. Test Full Pipeline with Dynamic Analysis")
    print("8. Test Transcription with Video File")
    print("9. Test Video Duration Detection")
    print("10. Test Stylized Pipeline (Choose Style)")
    print("11. Test Blog Avatar Pipeline (Choose Style)")
    print("12. Test Piwigo Image Upload")
    print("13. Show Test Results Summary")
    print("14. View Recent Logs")
    print("15. Check Environment Variables")
    print("16. Test VEO2 Image-to-Video Generation")
    print("17. Test ElevenLabs Audio Generation (Standalone)")
    print("18. Test Comprehensive End-to-End Pipeline")
    print("19. Test ASYNC Comprehensive Pipeline (⚡ Concurrent Processing)")
    print("20. Test Text-to-Blog Pipeline (25-second dialog)")
    print("0. Exit")
    print("=" * 50)

STYLE_OPTIONS = [
    ("ghibli", "Studio Ghibli"),
    ("pixar", "Pixar"),
    ("anime", "Anime"),
    ("watercolor", "Watercolor"),
    ("cyberpunk", "Cyberpunk"),
    ("realistic", "Realistic")
]
BLOG_STYLE_OPTIONS = [
    ("blog-female", "Blog (Female)"),
    ("blog-male", "Blog (Male)")
]

def select_style_menu(options, prompt="Select a style:"):
    print(f"\n{prompt}")
    for idx, (key, label) in enumerate(options, 1):
        print(f"{idx}. {label} ({key})")
    while True:
        choice = input(f"Enter your choice (1-{len(options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice)-1][0]
        print("❌ Invalid choice. Please try again.")

def generate_text_for_video_length(video_duration: float, input_text: str, job_id: str = None, key_phrases: list = None, third_person: bool = False, person_name: str = None) -> str:
    """
    Generate text using OpenAI GPT-4o that matches the length of a video when spoken.
    
    Args:
        video_duration (float): Duration of video in seconds (5-25 seconds)
        input_text (str): Input text/transcript to base the generated text on
        job_id (str): Optional job ID for logging
        key_phrases (list): Optional list of key phrases that represent the visual sequence
        third_person (bool): If True, generates third-person narration instead of first-person
        person_name (str): Name to use for third-person narration (defaults to generic names)
        
    Returns:
        str: Generated text that should match the video duration when spoken
    """
    print(f"\n🤖 Generating text for {video_duration:.2f} second video...")
    if third_person:
        print("📝 Generating third-person narration for blog avatar...")
    
    # Check if OpenAI API key is set
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")
    if not openai_key:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file")
        return ""
    
    # Set the API key
    openai.api_key = openai_key
    
    try:
        # Calculate approximate words needed based on average speaking rate
        # Average speaking rate is ~150-160 words per minute, so ~2.5 words per second
        target_words = int(video_duration * 2.5)
        
        # Determine the person name for third-person narration
        if third_person and not person_name:
            # Use generic names based on common names
            import random
            female_names = ["Sophie", "Emma", "Olivia", "Ava", "Isabella", "Sophia", "Charlotte", "Mia"]
            male_names = ["James", "Oliver", "Benjamin", "Elijah", "William", "Henry", "Alexander", "Michael"]
            person_name = random.choice(female_names + male_names)
        
        # Create a more targeted prompt if key phrases are provided
        if key_phrases and len(key_phrases) > 0:
            print(f"🎬 Creating narration for {len(key_phrases)} visual scenes...")
            
            # Create scene descriptions
            scene_descriptions = []
            for i, phrase in enumerate(key_phrases, 1):
                # Extract the core visual element from the phrase
                scene_desc = phrase.replace("A positive scene showing ", "").replace("A negative scene showing ", "").replace("A neutral scene showing ", "")
                scene_descriptions.append(f"Scene {i}: {scene_desc}")
            
            scenes_text = "\n".join(scene_descriptions)
            
            if third_person:
                prompt = f"""Based on the following original story and visual scenes, create a third-person narration about {person_name} that flows naturally through each scene in order. The narration should take approximately {video_duration:.1f} seconds to speak (around {target_words} words).

Original story (written in first person): "{input_text}"

Visual scenes in order:
{scenes_text}

Requirements:
- Convert the story to third-person perspective about {person_name}
- Change "I did..." to "{person_name} did..." throughout
- The narration should flow smoothly from scene to scene in the exact order listed above
- Should be approximately {target_words} words
- Should be engaging and narrative-style, like someone telling {person_name}'s story
- Should capture the essence and mood of the original story
- Should match the visual progression shown in the scenes
- Should flow naturally when spoken aloud
- Should be suitable for a video narration that follows the visual sequence

Create a flowing third-person narration that connects these scenes about {person_name}:"""
            else:
                prompt = f"""Based on the following original story and visual scenes, create a narration that flows naturally through each scene in order. The narration should take approximately {video_duration:.1f} seconds to speak (around {target_words} words).

Original story: "{input_text}"

Visual scenes in order:
{scenes_text}

Requirements:
- The narration should flow smoothly from scene to scene in the exact order listed above
- Should be approximately {target_words} words
- Should be engaging and narrative-style
- Should capture the essence and mood of the original story
- Should match the visual progression shown in the scenes
- Should flow naturally when spoken aloud
- Should be suitable for a video narration that follows the visual sequence

Create a flowing narration that connects these scenes:"""

        else:
            # Fallback to original approach if no key phrases provided
            if third_person:
                prompt = f"""Based on the following input text, create a third-person narrative about {person_name} that would take approximately {video_duration:.1f} seconds to speak (around {target_words} words).

Input text (written in first person): "{input_text}"

Requirements:
- Convert the story to third-person perspective about {person_name}
- Change "I did..." to "{person_name} did..." throughout  
- Change "my" to "{person_name}'s" and similar pronoun adjustments
- The output should be approximately {target_words} words
- Should be engaging and narrative-style, like someone telling {person_name}'s story
- Should capture the essence and mood of the input text
- Should flow naturally when spoken aloud
- Should be suitable for a video narration

Generated third-person text about {person_name}:"""
            else:
                prompt = f"""Based on the following input text, create a short narrative that would take approximately {video_duration:.1f} seconds to speak (around {target_words} words).

Input text: "{input_text}"

Requirements:
- The output should be approximately {target_words} words
- Should be engaging and narrative-style
- Should capture the essence and mood of the input text
- Should flow naturally when spoken aloud
- Should be suitable for a video narration

Generated text:"""

        # Call OpenAI GPT-4o
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a skilled storyteller who creates engaging narrations that match specific timing requirements and visual sequences. You excel at converting first-person stories to natural third-person narratives when requested."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=target_words + 50,  # Allow some buffer
            temperature=0.7
        )
        
        generated_text = response.choices[0].message.content.strip()
        word_count = len(generated_text.split())
        
        if third_person:
            print(f"✅ Generated third-person narration about {person_name} ({word_count} words):")
        else:
            print(f"✅ Generated sequence-aware text ({word_count} words):")
        print(f"   Preview: {generated_text[:100]}...")
        
        if key_phrases:
            print(f"   Matched to {len(key_phrases)} visual scenes")
        
        if job_id:
            logger.log_step(job_id, "TEXT_GENERATION", f"Generated {word_count} words for {video_duration:.2f}s video with {len(key_phrases) if key_phrases else 0} scenes", {
                "video_duration": video_duration,
                "target_words": target_words,
                "actual_words": word_count,
                "scene_count": len(key_phrases) if key_phrases else 0,
                "third_person": third_person,
                "person_name": person_name if third_person else None,
                "generated_text": generated_text
            })
        
        return generated_text
        
    except Exception as e:
        print(f"❌ OpenAI text generation failed: {e}")
        if job_id:
            logger.log_step(job_id, "TEXT_GENERATION_ERROR", f"Failed to generate text: {e}")
        return ""

def main():
    """Main interactive test loop."""
    tester = PipelineTester()
    video_paths = []
    audio_path = None
    
    # Show environment status on startup
    check_environment_variables()
    
    while True:
        show_menu()
        choice = input("Enter your choice (0-20): ").strip()
        
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
            tester.test_standalone_video_stitching()
        elif choice == "7":
            tester.create_test_job()  # Always create new job for full test
            tester.test_full_pipeline_with_sample_data()
        elif choice == "8":
            if not tester.job_id:
                tester.create_test_job()
            video_file = input("Enter path to video file: ").strip()
            if video_file:
                transcript = tester.test_transcription_with_file(video_file)
                if transcript:
                    duration = tester.test_video_duration(video_file)
                    if duration:
                        print(f"Video duration: {duration:.3f} seconds")
        elif choice == "9":
            if not tester.job_id:
                tester.create_test_job()
            video_file = input("Enter path to video file: ").strip()
            if video_file:
                duration = tester.test_video_duration(video_file)
                if duration:
                    print(f"✅ Video duration detected: {duration:.3f} seconds")
        elif choice == "10":
            if not tester.job_id:
                tester.create_test_job()
            style_key = select_style_menu(STYLE_OPTIONS, "Select a stylized/realistic style to test:")
            # Map to internal style string for test method
            style_map = {
                "ghibli": "Studio Ghibli",
                "pixar": "Pixar",
                "anime": "Anime",
                "watercolor": "Watercolor",
                "cyberpunk": "Cyberpunk",
                "realistic": "Realistic"
            }
            tester.test_stylized_pipeline(style_map[style_key])
        elif choice == "11":
            if not tester.job_id:
                tester.create_test_job()
            blog_style_key = select_style_menu(BLOG_STYLE_OPTIONS, "Select a blog avatar style to test:")
            blog_style_map = {
                "blog-female": "Blog (Female)",
                "blog-male": "Blog (Male)"
            }
            tester.test_blog_avatar_pipeline(blog_style_map[blog_style_key])
        elif choice == "12":
            tester.test_piwigo_upload()
        elif choice == "13":
            tester.print_results_summary()
        elif choice == "14":
            print("\n📜 Recent Logs:")
            print("-" * 30)
            try:
                with open("logs.txt", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    recent_lines = lines[-20:] if len(lines) > 20 else lines
                    print("".join(recent_lines))
            except FileNotFoundError:
                print("No log file found.")
        elif choice == "15":
            check_environment_variables()
        elif choice == "16":
            if not tester.job_id:
                tester.create_test_job()
            tester.test_veo2_image_to_video()
        elif choice == "17":
            if not tester.job_id:
                tester.create_test_job()
            tester.test_elevenlabs_audio_generation()
        elif choice == "18":
            if not tester.job_id:
                tester.create_test_job()
            tester.test_comprehensive_pipeline()
        elif choice == "19":
            if not tester.job_id:
                tester.create_test_job()
            tester.test_async_comprehensive_pipeline()
        elif choice == "20":
            if not tester.job_id:
                tester.create_test_job()
            # Add gender selection for text-to-blog test
            print("\nSelect gender for text-to-blog avatar:")
            print("1. Female")
            print("2. Male")
            while True:
                gender_choice = input("Enter your choice (1-2): ").strip()
                if gender_choice == "1":
                    selected_gender = "female"
                    break
                elif gender_choice == "2":
                    selected_gender = "male"
                    break
                print("❌ Invalid choice. Please try again.")
            tester.test_text_to_blog_pipeline(selected_gender)
        else:
            print("❌ Invalid choice. Please try again.")
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    print("🚀 Starting Pipeline Tester...")
    print("📊 Now featuring dynamic sentiment analysis and topic generation using GCP NLP!")
    
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