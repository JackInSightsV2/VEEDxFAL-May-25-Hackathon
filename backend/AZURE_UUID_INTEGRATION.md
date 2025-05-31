# Azure UUID Folder Integration

This document describes the enhanced Azure Storage integration that organizes uploaded files in UUID folders and automatically uploads final video outputs **with UUID-based filenames**.

## Features Added

### 1. UUID Folder Organization

All files uploaded to Azure Storage are now organized in UUID-based folders:

```
azure-container/
├── uuid-1/
│   ├── openai_image_0.png
│   ├── openai_image_1.png
│   ├── uuid-1.mp4              # Final video named with UUID
│   └── uuid-1_audio.mp3        # Final audio named with UUID
├── uuid-2/
│   ├── blog_blog_avatar_0.mp4
│   └── ...
└── uuid-3/
    └── ...
```

### 2. UUID-Based Filenames for Final Outputs

**Final files are now named using their UUID for easy identification:**
- **Final videos**: `{job_id}.mp4` (e.g., `abc-123-def.mp4`)
- **Final audio**: `{job_id}_audio.mp3` (e.g., `abc-123-def_audio.mp3`)
- **Other files**: Keep descriptive names (e.g., `openai_image_0.png`, `blog_avatar_0.mp4`)

### 3. Automatic Final Output Upload

The system now automatically uploads:
- **Final videos** (with audio narration) → Named as `{uuid}.mp4`
- **Blog avatar videos** → Keep descriptive names
- **Audio files** → Named as `{uuid}_audio.{ext}` for final audio
- **Generated images** → Keep descriptive names

All uploads are organized by job ID (UUID) for easy management.

## Updated Functions

### Enhanced Upload Functions

#### `upload_image(image_path, category_id=1, job_id=None)`
- **New parameter**: `job_id` - Optional job ID for folder organization
- **Behavior**: Creates `{job_id}/{filename}` structure in Azure
- **Auto-UUID**: Generates UUID if no job_id provided

#### `upload_video(video_path, job_id=None, video_type="video")`
- **UUID naming**: When `video_type="final"`, uses `{job_id}.mp4` as filename
- **Descriptive naming**: For other types, uses `{type}_{original_name}.mp4`
- **Examples**:
  - Final video: `abc-123/abc-123.mp4`
  - Blog video: `abc-123/blog_blog_avatar_0.mp4`
  - Clip video: `abc-123/clip_video_clip_0.mp4`

#### `upload_audio(audio_path, job_id=None, is_final=False)`
- **UUID naming**: When `is_final=True`, uses `{job_id}_audio.{ext}` as filename
- **Original naming**: For non-final audio, keeps original filename
- **Examples**:
  - Final audio: `abc-123/abc-123_audio.mp3`
  - Regular audio: `abc-123/voice.mp3`

#### `upload_final_outputs(job_id, final_video_path=None, audio_path=None)`
- **UUID-based naming**: Automatically uses UUID naming for final outputs
- **Returns**: Dictionary with Azure URLs using UUID filenames
- **Example URLs**:
  - `https://account.blob.core.windows.net/container/abc-123/abc-123.mp4`
  - `https://account.blob.core.windows.net/container/abc-123/abc-123_audio.mp3`

## Integration Points

### Main Pipeline Integration

All video generation endpoints now include Azure upload:

```python
# Upload final outputs to Azure Storage
logger.log_step(job_id, "AZURE_UPLOAD_START", "Uploading final video and audio to Azure Storage...")
try:
    azure_urls = upload_final_outputs(job_id, combined_video_path, audio_path)
    logger.log_step(job_id, "AZURE_UPLOAD_SUCCESS", f"Files uploaded to Azure: {list(azure_urls.keys())}")
except Exception as e:
    logger.log_step(job_id, "AZURE_UPLOAD_ERROR", f"Failed to upload to Azure: {e}")
    azure_urls = {}
```

### API Response Enhancement

All generation endpoints now return Azure URLs:

```json
{
    "job_id": "abc-123-def",
    "video": "/local/path/to/video.mp4",
    "azure_urls": {
        "final_video_url": "https://account.blob.core.windows.net/container/abc-123-def/abc-123-def.mp4",
        "audio_url": "https://account.blob.core.windows.net/container/abc-123-def/abc-123-def_audio.mp3"
    },
    ...
}
```

## File Types and Organization

### Stylized Videos (Studio Ghibli, Pixar, etc.)
- **Images**: `{job_id}/openai_image_{i}.png`
- **Video clips**: `{job_id}/video_clip_{i}.mp4`
- **Final video**: `{job_id}/{job_id}.mp4` ← **UUID filename**
- **Audio**: `{job_id}/{job_id}_audio.mp3` ← **UUID filename**

### Blog Avatar Videos
- **Blog video**: `{job_id}/blog_blog_avatar_0.mp4`
- **Note**: Blog videos include audio automatically and keep descriptive names

### Realistic Videos
- **Video clips**: `{job_id}/video_clip_{i}.mp4`
- **Final video**: `{job_id}/{job_id}.mp4` ← **UUID filename**
- **Audio**: `{job_id}/{job_id}_audio.mp3` ← **UUID filename**

## Benefits of UUID Filenames

1. **Unique identification**: Each final output has a globally unique filename
2. **Easy correlation**: Filename directly matches the job ID
3. **No conflicts**: UUID ensures no filename collisions
4. **Simplified referencing**: Can reference final output by job ID alone
5. **API consistency**: Job ID in response matches the actual filename

## Testing

### Test Script: `test_azure_uuid.py`

The test script now verifies UUID naming:

```bash
cd backend
python test_azure_uuid.py
```

**Updated tests**:
1. Azure configuration validation
2. Image upload with UUID folder
3. Video upload with type prefix
4. Audio upload with UUID folder
5. **UUID naming verification for final outputs**
6. Auto-UUID generation

### Expected Test Output

```
✅ Final video uses UUID as filename: abc-123-def.mp4
✅ Final audio uses UUID as filename: abc-123-def_audio.mp3
```

### Manual Testing

Test with the pipeline test script:

```bash
cd backend
python test_pipeline.py
```

Choose any pipeline test to verify Azure uploads are included.

## Configuration Required

Ensure these environment variables are set in your `.env` file:

```bash
AZURE_STORAGE_ACCOUNT=your_storage_account
AZURE_STORAGE_ACCOUNT_KEY=your_account_key
AZURE_STORAGE_CONTAINER=your_container_name
```

## Error Handling

- **Graceful degradation**: Pipeline continues even if Azure upload fails
- **Logging**: All upload attempts are logged with success/failure status
- **Partial uploads**: If some files fail, others may still succeed
- **Return values**: Empty `azure_urls` dict on failure

## Benefits

1. **Organization**: All files for a job are grouped together
2. **Scalability**: UUID-based folders prevent directory size issues
3. **Traceability**: Easy to find all files related to a specific job
4. **Backup**: Automatic cloud backup of all generated content
5. **Distribution**: Direct Azure CDN URLs for fast content delivery

## Usage Examples

### Direct Upload with UUID Naming
```python
from app.azure_uploader import upload_video, upload_audio, upload_final_outputs

# Upload final video (uses UUID as filename)
video_url = upload_video("my_video.mp4", job_id="abc-123", video_type="final")
# Result: https://storage.../abc-123/abc-123.mp4

# Upload final audio (uses UUID as filename)
audio_url = upload_audio("my_audio.mp3", job_id="abc-123", is_final=True)
# Result: https://storage.../abc-123/abc-123_audio.mp3

# Upload job outputs (automatically uses UUID naming)
azure_urls = upload_final_outputs("abc-123", "final.mp4", "audio.mp3")
# Results in UUID-based filenames
```

### Retrieving by UUID
```python
# Given a job_id, you can construct the final file URLs directly:
job_id = "abc-123-def"
final_video_url = f"https://account.blob.core.windows.net/container/{job_id}/{job_id}.mp4"
final_audio_url = f"https://account.blob.core.windows.net/container/{job_id}/{job_id}_audio.mp3"
``` 