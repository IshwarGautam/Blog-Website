import os
import re
import time
import base64
import tempfile
from googleapiclient.http import MediaFileUpload


def extract_base64_images(content):
    # Regex to find base64 image blocks - more flexible to handle TinyMCE format
    # Matches: <img src="data:image/TYPE;base64,DATA" ... >
    pattern = r'<img[^>]*src="(data:image/(png|jpeg|jpg|gif|webp);base64,[a-zA-Z0-9+/=]+)"[^>]*>'
    matches = re.findall(pattern, content)

    images = []
    for full_data_url, img_type in matches:
        # Try to extract filename from alt or title attribute, or generate one
        img_tag_match = re.search(
            r'<img[^>]*src="' + re.escape(full_data_url) + r'"[^>]*>',
            content
        )
        if img_tag_match:
            img_tag = img_tag_match.group(0)
            # Try to get filename from alt, title, or data-filename
            filename_match = re.search(
                r'(?:alt|title|data-filename)="([^"]+)"', img_tag
            )
            if filename_match:
                filename = filename_match.group(1)
                # Ensure it has an extension
                if not filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    filename = f"{filename}.{img_type}"
            else:
                # Generate a filename
                import hashlib
                hash_val = hashlib.md5(full_data_url.encode()).hexdigest()[:8]
                filename = f"image_{hash_val}.{img_type}"
        else:
            import hashlib
            hash_val = hashlib.md5(full_data_url.encode()).hexdigest()[:8]
            filename = f"image_{hash_val}.{img_type}"

        images.append(
            {
                "base64": full_data_url,
                "format": f"image/{img_type}",
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
