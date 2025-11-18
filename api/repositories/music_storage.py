from typing import Optional
from minio import Minio
from minio.error import S3Error

from api.core.config import settings


class StorageRepository:
    """Repository for MinIO storage operations."""

    def __init__(self, minio_client: Minio):
        self.client = minio_client
        self.bucket = settings.MINIO_BUCKET

    def object_exists(self, object_path: str) -> bool:
        try:
            self.client.stat_object(self.bucket, object_path)
            return True
        except S3Error:
            return False

    def get_object_size_in_bytes(self, object_path: str) -> int:
        stat = self.client.stat_object(self.bucket, object_path)
        return stat.size

    def get_object_stream(self, object_path: str, offset: Optional[int] = None, length: Optional[int] = None):
        """
        Get an object stream from MinIO.

        Args:
            object_path: Path to the object in the bucket
            offset: Optional byte offset to start reading from
            length: Optional number of bytes to read

        Returns:
            MinIO response object with stream() method

        Raises:
            S3Error: If object not found or other MinIO error
        """
        if offset is not None and length is not None:
            return self.client.get_object(self.bucket, object_path, offset=offset, length=length)
        return self.client.get_object(self.bucket, object_path)
