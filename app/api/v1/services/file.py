import os
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile, HTTPException, status

from app.core.configs import settings
from app.db.models.base import PyObjectId


class FileService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_STORAGE_ENDPOINT_URL  # Use custom endpoint
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.base_url = settings.AWS_STORAGE_ENDPOINT_URL

    async def _generate_file_key(self, prefix: str, file_name: str) -> str:
        """Generate unique file key with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_ext = os.path.splitext(file_name)[1]
        return f"{prefix}/{timestamp}_{file_name}"

    async def upload_file(self, file: UploadFile, prefix: str) -> str:
        """Generic file upload to S3 with enhanced error handling"""
        try:
            file.file.seek(0, 2)  # Seek to end to get size
            file_size = file.file.tell()
            file.file.seek(0)  # Reset pointer

            if file_size <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty"
                )

            file_key = await self._generate_file_key(prefix, file.filename)

            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                file_key,
                ExtraArgs={
                    'ContentType': file.content_type,
                    'ACL': 'public-read'
                }
            )
            return f"{self.base_url}/{self.bucket_name}/{file_key}"

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == 'AccessDenied':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="S3 access denied - check permissions"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 upload failed: {str(e)}"
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"File upload failed: {str(e)}"
            )

    async def upload_avatar(self, avatar: UploadFile, user_id: PyObjectId) -> str:
        """Upload user avatar to S3"""
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if avatar.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG, PNG, and GIF images are allowed"
            )

        if avatar.size > 5 * 1024 * 1024:  # 5MB limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Avatar image too large (max 5MB)"
            )

        return await self.upload_file(avatar, f"avatars/{user_id}")

    async def upload_report_attachment(self, file: UploadFile, report_id: PyObjectId) -> str:
        """Upload report attachment to S3"""
        max_size = 10 * 1024 * 1024  # 10MB limit
        if file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large (max {max_size // (1024 * 1024)}MB)"
            )

        return await self.upload_file(file, f"reports/{report_id}/attachments")

    async def delete_file(self, file_url: str) -> bool:
        """Delete file from S3"""
        try:
            # Extract key from URL
            key = file_url.replace(f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/", "")
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )

    async def generate_presigned_url(self, file_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL using custom endpoint"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            # Replace the default endpoint with our custom one if needed
            if "amazonaws.com" in url:
                url = url.replace(
                    f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com",
                    settings.aws_s3_endpoint_url.rstrip('/')
                )
            return url
        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )


def get_file_service() -> FileService:
    return FileService()
