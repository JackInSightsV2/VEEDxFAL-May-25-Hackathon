import os
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


def upload_image(image_path: str, category_id: int = 1) -> str:
    """
    Uploads an image to Azure Blob Storage and returns the public URL.
    The category_id argument is ignored for Azure but kept for compatibility.
    """
    container_client = blob_service_client.get_container_client(AZURE_STORAGE_CONTAINER)
    blob_name = os.path.basename(image_path)

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

# === Example usage ===
if __name__ == "__main__":
    image_path = "yourfile.jpg"  # Replace this with your file path
    try:
        url = upload_image(image_path)
        print("✅ Public image URL:", url)
    except Exception as e:
        print("❌ Error:", e) 