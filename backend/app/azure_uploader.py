import os
import uuid
from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER")

if not AZURE_STORAGE_ACCOUNT or not AZURE_STORAGE_ACCOUNT_KEY or not AZURE_STORAGE_CONTAINER:
    raise Exception("Missing Azure Storage configuration in environment variables.")

# Construct the Blob Service Client
blob_service_client = BlobServiceClient(
    account_url=f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=AZURE_STORAGE_ACCOUNT_KEY
)


def upload_image(image_path: str, category_id: int = 1, job_id: str = None) -> str:
    """
    Uploads an image to Azure Blob Storage in a UUID folder and returns the public URL.
    The category_id argument is ignored for Azure but kept for compatibility.
    
    Args:
        image_path (str): Path to the image file
        category_id (int): Ignored for Azure, kept for compatibility
        job_id (str): Optional job ID to use as folder name, generates UUID if not provided
        
    Returns:
        str: Public URL of the uploaded image
    """
    container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
    
    # Generate UUID folder if job_id not provided
    folder_id = job_id if job_id else str(uuid.uuid4())
    
    # Create blob name with UUID folder structure
    filename = os.path.basename(image_path)
    blob_name = f"{folder_id}/{filename}"

    # Upload the image
    with open(image_path, "rb") as data:
        container_client.upload_blob(
            name=blob_name,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type="image/png")
        )

    # Construct the public URL
    public_url = f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{AZURE_STORAGE_CONTAINER}/{blob_name}"
    print(f"[Azure] Uploaded image URL: {public_url}")
    return public_url


def upload_video(video_path: str, job_id: str = None, video_type: str = "video") -> str:
    """
    Uploads a video file to Azure Blob Storage in a UUID folder and returns the public URL.
    
    Args:
        video_path (str): Path to the video file
        job_id (str): Optional job ID to use as folder name, generates UUID if not provided
        video_type (str): Type of video (e.g., "final", "blog", "clip") for naming
        
    Returns:
        str: Public URL of the uploaded video
    """
    container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
    
    # Generate UUID folder if job_id not provided
    folder_id = job_id if job_id else str(uuid.uuid4())
    
    # Get file extension
    file_extension = os.path.splitext(video_path)[1]
    
    # For final videos, use UUID as filename; otherwise use original name with prefix
    if video_type == "final" and job_id:
        filename = f"{job_id}{file_extension}"
    else:
        # Use original filename logic for non-final videos
        filename = os.path.basename(video_path)
        if video_type != "video":
            name_parts = os.path.splitext(filename)
            filename = f"{video_type}_{name_parts[0]}{name_parts[1]}"
    
    blob_name = f"{folder_id}/{filename}"

    # Upload the video
    with open(video_path, "rb") as data:
        container_client.upload_blob(
            name=blob_name,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type="video/mp4")
        )

    # Construct the public URL
    public_url = f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{AZURE_STORAGE_CONTAINER}/{blob_name}"
    print(f"[Azure] Uploaded video URL: {public_url}")
    return public_url


def upload_audio(audio_path: str, job_id: str = None, is_final: bool = False) -> str:
    """
    Uploads an audio file to Azure Blob Storage in a UUID folder and returns the public URL.
    
    Args:
        audio_path (str): Path to the audio file
        job_id (str): Optional job ID to use as folder name, generates UUID if not provided
        is_final (bool): Whether this is a final audio file (uses UUID as filename)
        
    Returns:
        str: Public URL of the uploaded audio
    """
    container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
    
    # Generate UUID folder if job_id not provided
    folder_id = job_id if job_id else str(uuid.uuid4())
    
    # Get file extension
    file_extension = os.path.splitext(audio_path)[1]
    
    # For final audio, use UUID as filename; otherwise use original name
    if is_final and job_id:
        filename = f"{job_id}_audio{file_extension}"
    else:
        filename = os.path.basename(audio_path)
    
    blob_name = f"{folder_id}/{filename}"

    # Determine content type based on file extension
    file_ext = os.path.splitext(filename)[1].lower()
    content_type = "audio/mpeg" if file_ext == ".mp3" else "audio/wav"

    # Upload the audio
    with open(audio_path, "rb") as data:
        container_client.upload_blob(
            name=blob_name,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )

    # Construct the public URL
    public_url = f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{AZURE_STORAGE_CONTAINER}/{blob_name}"
    print(f"[Azure] Uploaded audio URL: {public_url}")
    return public_url


def upload_file_generic(file_path: str, job_id: str = None, file_type: str = None) -> str:
    """
    Generic file upload function that uploads any file to Azure Blob Storage in a UUID folder.
    
    Args:
        file_path (str): Path to the file
        job_id (str): Optional job ID to use as folder name, generates UUID if not provided
        file_type (str): Optional file type for content-type detection
        
    Returns:
        str: Public URL of the uploaded file
    """
    container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
    
    # Generate UUID folder if job_id not provided
    folder_id = job_id if job_id else str(uuid.uuid4())
    
    # Create blob name with UUID folder structure
    filename = os.path.basename(file_path)
    blob_name = f"{folder_id}/{filename}"

    # Determine content type
    content_type = "application/octet-stream"  # Default
    file_ext = os.path.splitext(filename)[1].lower()
    
    if file_type:
        if file_type.startswith("video"):
            content_type = "video/mp4"
        elif file_type.startswith("audio"):
            content_type = "audio/mpeg"
        elif file_type.startswith("image"):
            content_type = "image/png"
    else:
        # Auto-detect based on extension
        if file_ext in [".mp4", ".avi", ".mov", ".webm"]:
            content_type = "video/mp4"
        elif file_ext in [".mp3", ".wav", ".aac"]:
            content_type = "audio/mpeg"
        elif file_ext in [".png", ".jpg", ".jpeg", ".gif"]:
            content_type = "image/png"
        elif file_ext in [".txt", ".log"]:
            content_type = "text/plain"
        elif file_ext in [".json"]:
            content_type = "application/json"

    # Upload the file
    with open(file_path, "rb") as data:
        container_client.upload_blob(
            name=blob_name,
            data=data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )

    # Construct the public URL
    public_url = f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{AZURE_STORAGE_CONTAINER}/{blob_name}"
    print(f"[Azure] Uploaded file URL: {public_url}")
    return public_url


def upload_final_outputs(job_id: str, final_video_path: str = None, audio_path: str = None) -> dict:
    """
    Upload final outputs (video and audio) to Azure Storage for a completed job.
    Files are named using the UUID for easy identification.
    
    Args:
        job_id (str): Job ID to use as the folder name and filename base
        final_video_path (str): Path to the final video file
        audio_path (str): Path to the audio file
        
    Returns:
        dict: Dictionary containing the URLs of uploaded files
    """
    uploaded_urls = {}
    
    try:
        if final_video_path and os.path.exists(final_video_path):
            video_url = upload_video(final_video_path, job_id, "final")
            uploaded_urls["final_video_url"] = video_url
            print(f"✅ Final video uploaded with UUID name: {video_url}")
        
        if audio_path and os.path.exists(audio_path):
            audio_url = upload_audio(audio_path, job_id, is_final=True)
            uploaded_urls["audio_url"] = audio_url
            print(f"✅ Final audio uploaded with UUID name: {audio_url}")
            
        return uploaded_urls
        
    except Exception as e:
        print(f"❌ Error uploading final outputs: {e}")
        return uploaded_urls


def list_mp4_videos() -> list[dict]:
    """
    Lists all .mp4 video files from Azure Blob Storage.
    
    Returns:
        list[dict]: List of dictionaries containing video information
                   Each dict contains: {'name': str, 'url': str, 'size': int, 'last_modified': str}
    """
    try:
        container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
        videos = []
        
        # List all blobs in the container
        blobs = container_client.list_blobs()
        
        for blob in blobs:
            # Only include .mp4 files
            if blob.name.endswith('.mp4'):
                # Construct the public URL
                public_url = f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{AZURE_STORAGE_CONTAINER}/{blob.name}"
                
                videos.append({
                    'name': blob.name,
                    'url': public_url,
                    'size': blob.size,
                    'last_modified': blob.last_modified.isoformat() if blob.last_modified else None
                })
        
        print(f"[Azure] Found {len(videos)} .mp4 files")
        return videos
        
    except Exception as e:
        print(f"❌ Error listing videos from Azure: {e}")
        return []


# === Example usage ===
if __name__ == "__main__":
    image_path = "yourfile.jpg"  # Replace this with your file path
    try:
        url = upload_image(image_path)
        print("✅ Public image URL:", url)
    except Exception as e:
        print("❌ Error:", e) 