import os
import re
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

PIWIGO_URL = os.getenv("PIWIGO_URL")
USERNAME = os.getenv("PIWIGO_USER")
PASSWORD = os.getenv("PIWIGO_PASS")

def upload_image(image_path: str, category_id: int = 1) -> str:
    session = requests.Session()

    # 1. Login
    login_data = {
        "method": "pwg.session.login",
        "username": USERNAME,
        "password": PASSWORD
    }
    r = session.post(PIWIGO_URL, data=login_data)
    print("[Piwigo] Login response:", r.text)
    try:
        r.raise_for_status()
        login_json = r.json()
    except Exception as e:
        raise Exception(f"Piwigo login failed: {e}\nRaw response: {r.text}")
    if login_json.get("stat") != "ok":
        raise Exception(f"Login failed: {login_json}")

    # 2. Get session token
    r = session.post(PIWIGO_URL, data={"method": "pwg.session.getStatus"})
    r.raise_for_status()
    session_info = r.json()
    token = session_info["result"]["pwg_token"]
    print("[Piwigo] Session token:", token)

    # 3. Upload Image
    with open(image_path, "rb") as img_file:
        files = {"file": img_file}
        upload_data = {
            "method": "pwg.images.upload",
            "category": str(category_id),
            "name": os.path.basename(image_path),
            "pwg_token": token
        }
        r = session.post(PIWIGO_URL, data=upload_data, files=files)
        print("[Piwigo] Upload response:", r.text)
        try:
            r.raise_for_status()
            # Clean mixed HTML warnings from JSON
            cleaned = re.search(r'({.*})', r.text, re.DOTALL)
            if not cleaned:
                raise Exception("No valid JSON found in response.")
            result = json.loads(cleaned.group(1))
        except Exception as e:
            raise Exception(f"Piwigo image upload failed: {e}\nRaw response: {r.text}")
        if result.get("stat") != "ok":
            raise Exception(f"Upload failed: {result}")
        image_id = result["result"]["image_id"]

    # 4. Get full image info
    r = session.post(PIWIGO_URL, data={
        "method": "pwg.images.getInfo",
        "image_id": image_id
    })
    r.raise_for_status()
    info = r.json()
    # Prefer direct full-size image URL if available
    derivatives = info["result"].get("derivatives", {})
    full_url = None
    for quality in ["xxlarge", "xlarge", "large", "medium", "original"]:
        if quality in derivatives:
            full_url = derivatives[quality]["url"]
            break
    # Fallback to display page
    if not full_url:
        full_url = info["result"]["element_url"]
    full_url = full_url.replace("\\/", "/")
    print(f"[Piwigo] Full image URL: {full_url}")

    # 5. Logout
    try:
        logout_resp = session.post(PIWIGO_URL, data={"method": "pwg.session.logout"})
        print("[Piwigo] Logout response:", logout_resp.text)
    except Exception as e:
        print(f"[Piwigo] Logout failed: {e}")

    return full_url

# === Example usage ===
if __name__ == "__main__":
    image_path = "yourfile.jpg"  # Replace this with your file path
    try:
        url = upload_image(image_path)
        print("✅ Full-size image URL:", url)
    except Exception as e:
        print("❌ Error:", e)
