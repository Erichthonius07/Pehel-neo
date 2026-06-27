"""Storage service for photo uploads using MinIO/S3 presigned URLs.

Uses MinIO (S3-compatible) for object storage.
Generates presigned PUT URLs for direct upload from client.
"""

import uuid
from datetime import timedelta
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings

settings = get_settings()

# MinIO/S3 client
_s3_client = None


def _get_s3_client():
    """Lazy-init S3 client for MinIO."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT or "http://localhost:9000",
            aws_access_key_id=settings.MINIO_ACCESS_KEY or "minioadmin",
            aws_secret_access_key=settings.MINIO_SECRET_KEY or "minioadmin",
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
    return _s3_client


def _get_bucket_name() -> str:
    """Get bucket name from settings."""
    return getattr(settings, "MINIO_BUCKET", "pehel-neo")


def ensure_bucket():
    """Ensure the bucket exists."""
    client = _get_s3_client()
    bucket = _get_bucket_name()
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)


def generate_upload_url(
    issue_id: uuid.UUID,
    media_type: str = "complaint_photo",
    content_type: str = "image/jpeg",
    expiry_seconds: int = 300,
) -> dict:
    """Generate a presigned PUT URL for direct client upload.
    
    Args:
        issue_id: The issue UUID
        media_type: complaint_photo|resolution_photo|visit_photo|audio
        content_type: MIME type of the file
        expiry_seconds: URL expiry time
    
    Returns:
        {
            "upload_url": "https://...",
            "public_url": "https://...",
            "s3_key": "issues/{issue_id}/{media_type}/{uuid}.jpg"
        }
    """
    client = _get_s3_client()
    bucket = _get_bucket_name()
    ensure_bucket()

    ext = "jpg" if "jpeg" in content_type else ("png" if "png" in content_type else "bin")
    object_key = f"issues/{issue_id}/{media_type}/{uuid.uuid4()}.{ext}"

    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=expiry_seconds,
    )

    public_url = f"{settings.MINIO_ENDPOINT or 'http://localhost:9000'}/{bucket}/{object_key}"

    return {
        "upload_url": upload_url,
        "public_url": public_url,
        "s3_key": object_key,
        "s3_bucket": bucket,
    }


def generate_read_url(s3_key: str, expiry_seconds: int = 3600) -> str:
    """Generate a presigned GET URL for reading an object."""
    client = _get_s3_client()
    bucket = _get_bucket_name()

    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )
