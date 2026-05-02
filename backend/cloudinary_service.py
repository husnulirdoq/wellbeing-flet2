import cloudinary
import cloudinary.uploader
import os

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY    = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

def configure():
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )

def upload_image(file_bytes: bytes, filename: str = "product") -> str:
    configure()
    result = cloudinary.uploader.upload(
        file_bytes,
        folder="wellbeing/products",
        public_id=filename,
        overwrite=True,
        resource_type="image",
    )
    return result.get("secure_url", "")
