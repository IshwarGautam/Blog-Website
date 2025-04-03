import os
import re
import time
import base64
import tempfile
from googleapiclient.http import MediaFileUpload


def extract_base64_images(content):
    # Regex to find base64 image data
    pattern = r"base64,([a-zA-Z0-9+/=]+)"
    base64_images = re.findall(pattern, content)
    print(content)
    images = []
    for image_data in base64_images:
        # Identify image format from the content (e.g., image/png, image/jpeg)
        if content.find(f"data:image/png;base64,{image_data}") != -1:
            img_format = "image/png"
        elif content.find(f"data:image/jpeg;base64,{image_data}") != -1:
            img_format = "image/jpeg"
        else:
            img_format = "image/jpeg"  # Default to JPEG if not found

        # Get file name
        filename_match = re.search(r'data-filename="([^"]+)"', content)
        filename = filename_match.group(1) if filename_match else "image.png"
        images.append(
            {
                "base64": f"data:{img_format};base64,{image_data}",
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
