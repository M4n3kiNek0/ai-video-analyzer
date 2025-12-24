"""
Storage Service for MinIO (Local Object Storage).
Handles uploading keyframes and videos to MinIO.
"""

import os
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinIOStorage:
    """
    MinIO storage handler for video screenshots and assets.
    Uses boto3 with S3-compatible API for MinIO.
    """

    def __init__(self):
        """Initialize MinIO client with credentials from environment."""
        self.endpoint_url = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
        self.public_endpoint = os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000")
        self.bucket = os.getenv("MINIO_BUCKET", "video-screenshots")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
        
        if not self.access_key or not self.secret_key:
            raise ValueError(
                "MINIO_ACCESS_KEY and MINIO_SECRET_KEY must be set in environment"
            )
        
        # Configure boto3 for MinIO compatibility
        config = Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}  # Required for MinIO
        )
        
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="us-east-1",  # Required by boto3, ignored by MinIO
            config=config
        )
        
        logger.info(f"MinIOStorage initialized: endpoint={self.endpoint_url}, bucket={self.bucket}")
        
        # Ensure bucket exists
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket '{self.bucket}' exists")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ['404', 'NoSuchBucket']:
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                    logger.info(f"Created bucket '{self.bucket}'")
                    
                    # Set bucket policy for public read access
                    self._set_public_read_policy()
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise

    def _set_public_read_policy(self) -> None:
        """Set bucket policy for public read access (useful for MinIO)."""
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket}/*"]
                }
            ]
        }
        
        try:
            import json
            self.client.put_bucket_policy(
                Bucket=self.bucket,
                Policy=json.dumps(policy)
            )
            logger.info(f"Public read policy set on bucket '{self.bucket}'")
        except ClientError as e:
            logger.warning(f"Could not set bucket policy: {e}")

    def upload_keyframe(
        self,
        local_path: str,
        video_id: int,
        keyframe_num: int
    ) -> str:
        """
        Upload a keyframe image to S3/MinIO.
        
        Args:
            local_path: Path to local image file
            video_id: Video ID for organizing files
            keyframe_num: Keyframe sequence number
            
        Returns:
            Public URL of uploaded file
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")
        
        # Generate S3 key
        s3_key = f"videos/{video_id}/keyframes/keyframe_{keyframe_num:03d}.jpg"
        
        try:
            # Upload with content type
            self.client.upload_file(
                local_path,
                self.bucket,
                s3_key,
                ExtraArgs={
                    "ContentType": "image/jpeg",
                    "ACL": "public-read"  # Make file publicly accessible
                }
            )
            
            # Generate public URL
            # Use public endpoint if configured (for browser access), otherwise internal endpoint
            base_url = self.public_endpoint or self.endpoint_url
            url = f"{base_url}/{self.bucket}/{s3_key}"
            
            logger.info(f"Uploaded keyframe: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            raise
        except NoCredentialsError:
            logger.error("S3 credentials not configured")
            raise

    def upload_video(
        self,
        local_path: str,
        video_id: int,
        filename: Optional[str] = None
    ) -> str:
        """
        Upload original video to S3/MinIO.
        
        Args:
            local_path: Path to local video file
            video_id: Video ID for organizing files
            filename: Optional custom filename
            
        Returns:
            Public URL of uploaded file
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")
        
        # Determine filename and extension
        if filename:
            ext = os.path.splitext(filename)[1] or ".mp4"
        else:
            ext = os.path.splitext(local_path)[1] or ".mp4"
        
        s3_key = f"videos/{video_id}/original{ext}"
        
        # Determine content type
        content_types = {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".avi": "video/x-msvideo",
            ".mkv": "video/x-matroska",
            ".webm": "video/webm"
        }
        content_type = content_types.get(ext.lower(), "video/mp4")
        
        try:
            self.client.upload_file(
                local_path,
                self.bucket,
                s3_key,
                ExtraArgs={
                    "ContentType": content_type
                }
            )
            
            url = f"{self.endpoint_url}/{self.bucket}/{s3_key}"
            
            logger.info(f"Uploaded video: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Video upload failed: {e}")
            raise

    def upload_audio(
        self,
        local_path: str,
        video_id: int
    ) -> str:
        """
        Upload extracted audio to MinIO.
        
        Args:
            local_path: Path to local audio file
            video_id: Video ID for organizing files
            
        Returns:
            Public URL of uploaded file
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")
        
        ext = os.path.splitext(local_path)[1] or ".mp3"
        s3_key = f"videos/{video_id}/audio{ext}"
        
        content_types = {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4"
        }
        content_type = content_types.get(ext.lower(), "audio/mpeg")
        
        try:
            self.client.upload_file(
                local_path,
                self.bucket,
                s3_key,
                ExtraArgs={"ContentType": content_type}
            )
            
            url = f"{self.endpoint_url}/{self.bucket}/{s3_key}"
            logger.info(f"Uploaded audio: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Audio upload failed: {e}")
            raise

    def delete_video_assets(self, video_id: int) -> bool:
        """
        Delete all assets for a video from MinIO.
        
        Args:
            video_id: Video ID
            
        Returns:
            True if successful
        """
        prefix = f"videos/{video_id}/"
        
        try:
            # List all objects with prefix
            response = self.client.list_objects_v2(
                Bucket=self.bucket,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                logger.info(f"No objects found for video {video_id}")
                return True
            
            # Delete all objects
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            
            self.client.delete_objects(
                Bucket=self.bucket,
                Delete={'Objects': objects_to_delete}
            )
            
            logger.info(f"Deleted {len(objects_to_delete)} objects for video {video_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Delete failed: {e}")
            return False

    def get_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> str:
        """
        Generate a presigned URL for temporary access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Presigned URL generation failed: {e}")
            raise

    def check_connection(self) -> bool:
        """
        Test MinIO connection.
        
        Returns:
            True if connection successful
        """
        try:
            self.client.list_buckets()
            return True
        except Exception as e:
            logger.error(f"MinIO connection check failed: {e}")
            return False


def test_storage_connection() -> bool:
    """
    Test storage connection and bucket access.
    
    Returns:
        True if successful
    """
    try:
        storage = MinIOStorage()
        return storage.check_connection()
    except Exception as e:
        logger.error(f"Storage test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing MinIO connection...")
    if test_storage_connection():
        print("✓ MinIO connection successful")
    else:
        print("✗ MinIO connection failed")
        print("  Make sure MinIO is running: docker-compose up -d minio")
