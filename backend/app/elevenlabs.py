"""Voice generation module using ElevenLabs API."""

import os
from .logger import logger

try:
    from elevenlabs import ElevenLabs
    HAS_ELEVENLABS = True
except ImportError:
    HAS_ELEVENLABS = False
    print("⚠️ ElevenLabs SDK not installed. Install with: pip install elevenlabs")


def generate_voice(script: str, job_id: str = None, voice_id: str = None, gender: str = None) -> str:
    """Generate an audio file from the script using ElevenLabs API."""
    
    if not HAS_ELEVENLABS:
        raise ImportError("ElevenLabs SDK not installed. Install with: pip install elevenlabs")
    
    # Get API key
    api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
    if not api_key:
        raise ValueError("ElevenLabs API key not found. Please set ELEVENLABS_API_KEY or ELEVEN_API_KEY in your .env file")
    
    # Define voice mappings
    VOICE_MAP = {
        "female": {
            "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella - warm, friendly female voice
            "name": "Bella"
        },
        "male": {
            "voice_id": "VR6AewLTigWG4xSOukaG",  # Josh - clear, confident male voice  
            "name": "Josh"
        },
        "non-binary": {
            "voice_id": "JBFqnCBsd6RMkjVDRZzb",  # George - neutral voice
            "name": "George"
        },
        "nonbinary": {
            "voice_id": "JBFqnCBsd6RMkjVDRZzb",  # George - neutral voice (alternative key)
            "name": "George"
        },
        "default": {
            "voice_id": "JBFqnCBsd6RMkjVDRZzb",  # George - neutral voice
            "name": "George"
        }
    }
    
    # Determine which voice to use
    if voice_id:
        # Use provided voice ID
        selected_voice_id = voice_id
        voice_name = "Custom"
    elif gender and gender.lower() in VOICE_MAP:
        # Use gender-appropriate voice
        voice_info = VOICE_MAP[gender.lower()]
        selected_voice_id = voice_info["voice_id"]
        voice_name = voice_info["name"]
    else:
        # Use default voice
        voice_info = VOICE_MAP["default"]
        selected_voice_id = voice_info["voice_id"]
        voice_name = voice_info["name"]
    
    print(f"🎵 Generating audio with ElevenLabs...")
    print(f"   Voice: {voice_name} ({selected_voice_id})")
    if gender:
        print(f"   Gender: {gender}")
    print(f"   Text length: {len(script)} characters")
    print(f"   Text preview: {script[:100]}...")
    
    try:
        # Initialize ElevenLabs client
        client = ElevenLabs(api_key=api_key)
        
        # Generate audio
        print("🔊 Calling ElevenLabs API...")
        audio_generator = client.text_to_speech.convert(
            voice_id=selected_voice_id,
            output_format="mp3_44100_128",
            text=script,
            model_id="eleven_multilingual_v2",
        )
        
        # Determine output path
        if job_id:
            audio_path = logger.get_job_file_path(job_id, "voice.mp3")
        else:
            audio_path = "voice.mp3"
        
        print(f"💾 Saving audio to: {audio_path}")
        
        # Save the audio file
        with open(audio_path, "wb") as f:
            for chunk in audio_generator:
                f.write(chunk)
        
        # Verify file was created and has content
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"✅ Audio file created successfully!")
            print(f"   File path: {audio_path}")
            print(f"   File size: {file_size} bytes ({file_size / 1024:.2f} KB)")
            print(f"   Voice used: {voice_name}")
            
            if file_size == 0:
                raise ValueError("Generated audio file is empty")
            
            # Log success
            if job_id:
                logger.log_step(job_id, "AUDIO_GENERATION_SUCCESS", f"ElevenLabs audio generated with {voice_name} voice: {file_size} bytes")
            
            return audio_path
        else:
            raise FileNotFoundError(f"Audio file was not created at {audio_path}")
    
    except Exception as e:
        error_msg = f"ElevenLabs audio generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Log error
        if job_id:
            logger.log_step(job_id, "AUDIO_GENERATION_ERROR", error_msg)
        
        # Re-raise the exception so calling code can handle it
        raise e
