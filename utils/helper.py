import os
import re
import time
import base64
import tempfile
from googleapiclient.http import MediaFileUpload


def extract_base64_images(content):
    # Regex to find base64 image blocks with their filenames
    pattern = (
        r'data:(image/(?:png|jpeg));base64,([a-zA-Z0-9+/=]+)".*?data-filename="([^"]+)"'
    )
    matches = re.findall(pattern, content)

    images = []
    for img_format, base64_data, filename in matches:
        images.append(
            {
                "base64": f"data:{img_format};base64,{base64_data}",
                "format": img_format,
                "filename": filename,
            }
        )
    return images


def upload_image_to_google_drive(
    base64_data, img_format, drive_service, FOLDER_ID, filename
):
    # Remove base64 prefix (data:image/png;base64,)
    image_data = base64_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)

    # Save image to a temporary file with the correct extension (JPG or PNG)
    suffix = filename.split(".")[-1]
    temp_image_path = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_image_path.write(image_bytes)
    temp_image_path.close()  # Ensure the file is closed so we can access it later

    # Upload the image to Google Drive
    file_metadata = {"name": filename, "parents": [FOLDER_ID]}
    media = MediaFileUpload(temp_image_path.name, mimetype=img_format)
    uploaded_file = (
        drive_service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    file_id = uploaded_file.get("id")
    file_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"

    # Clean up the temporary image file
    del media  # Force garbage collection of the MediaFileUpload object
    time.sleep(1)  # Give it some time
    os.remove(temp_image_path.name)

    return file_url


def delete_image_from_google_drive(drive_service, file_id):
    try:
        drive_service.files().delete(fileId=file_id).execute()
        print(f"Deleted image {file_id} from Google Drive")
        return True
    except Exception as e:
        print(f"Error deleting image {file_id}: {e}")
        return False
