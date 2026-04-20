# image_utils.py: 
import uuid
from io import BytesIO
import boto3
from starlette.concurrency import run_in_threadpool
from config import settings

from PIL import Image, ImageOps
# ^ Pillow library for image processing, install with: pip install Pillow, when handling images in FastAPI, you typically receive them as UploadFile.
# the original library, PIL, was discontinued years ago. The community created Pillow as a drop-in replacement.


def _get_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        aws_access_key_id=(
            settings.s3_access_key_id.get_secret_value()
            if settings.s3_access_key_id
            else None
        ),
        aws_secret_access_key=(
            settings.s3_secret_access_key.get_secret_value()
            if settings.s3_secret_access_key
            else None
        ),
        endpoint_url=settings.s3_endpoint_url,
        config=boto3.session.Config(signature_version='s3v4'),  # because boto3 might use a signature format that MinIO doesn't understand, causing authentication errors.
    )


def process_profile_image(content: bytes) -> tuple[bytes, str]:
    """
    It receives the image as raw bytes (usually from UploadFile.read() in FastAPI).
    It returns a filename (string) that you store in your database.
    """
    with Image.open(BytesIO(content)) as original:        
        """
        BytesIO(content) turns raw bytes into a file-like object.
        Image.open() (from Pillow) reads that file-like object as an image.
        The with block ensures the image file is properly closed afterward.
        """
        img = ImageOps.exif_transpose(original)
        """
        Many mobile photos contain EXIF orientation metadata instead of actually rotating the pixels.
        Without this: Some images may appear sideways or upside down.
        exif_transpose(): Reads EXIF rotation info,  Rotates the image correctly, Removes the orientation tag, This prevents weird profile pictures.
        """

        img = ImageOps.fit(img, (300, 300), method=Image.Resampling.LANCZOS)
        """
        Resizes the image, Crops it if necessary, Ensures final size is exactly 300x300, It preserves aspect ratio and center-crops if needed.
        Image.Resampling.LANCZOS: High-quality downscaling filter, Produces sharp results, Best choice for profile images
        """
        # Convert to RGB (remove transparency), JPEG does not support transparency.
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        filename = f"{uuid.uuid4().hex}.jpg"
        output = BytesIO()
        img.save(output, "JPEG", quality=85, optimize=True)
        output.seek(0)

    return output.read(), filename

"""
function summary:
✔ Correct orientation
✔ Cropped square
✔ 300x300 size
✔ Converted to JPEG
✔ No transparency
✔ Optimized file size
✔ Unique safe filename
✔ Stored in correct directory
"""

def _upload_to_s3(file_bytes: bytes, key: str) -> None:
    s3 = _get_s3_client()
    s3.upload_fileobj(
        BytesIO(file_bytes),
        settings.s3_bucket_name,
        key,
        ExtraArgs={"ContentType": "image/jpeg"},
    )


def _delete_from_s3(key: str) -> None:
    s3 = _get_s3_client()
    s3.delete_object(Bucket=settings.s3_bucket_name, Key=key)


async def upload_profile_image(file_bytes: bytes, filename: str) -> None:
    key = f"profile_pics/{filename}"
    await run_in_threadpool(_upload_to_s3, file_bytes, key)


async def delete_profile_image(filename: str | None) -> None:
    if filename is None:
        return
    key = f"profile_pics/{filename}"
    await run_in_threadpool(_delete_from_s3, key)