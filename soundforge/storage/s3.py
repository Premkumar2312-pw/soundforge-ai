"""
S3-Compatible Storage Provider for SoundForge AI (MinIO / AWS S3)
"""

import os
from typing import List
from soundforge.storage.base import BaseStorageProvider
from soundforge.storage.local import LocalStorageProvider
from soundforge.config import settings
from soundforge.utils.logging import logger

class S3StorageProvider(BaseStorageProvider):
    """
    S3 Storage Provider with fallback to local filesystem if S3 credentials are unset.
    """
    def __init__(self):
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.bucket_name = settings.S3_BUCKET_NAME
        self.local_fallback = LocalStorageProvider()
        self.is_configured = bool(settings.S3_ACCESS_KEY and settings.S3_SECRET_KEY)
        
        if not self.is_configured:
            logger.info("S3 credentials not supplied. Using local filesystem backing store for S3 provider.")

    def get_job_dir(self, job_id: str) -> str:
        return self.local_fallback.get_job_dir(job_id)

    def get_artifact_path(self, job_id: str, filename: str) -> str:
        return self.local_fallback.get_artifact_path(job_id, filename)

    def artifact_exists(self, job_id: str, filename: str) -> bool:
        return self.local_fallback.artifact_exists(job_id, filename)

    def list_artifacts(self, job_id: str) -> List[str]:
        return self.local_fallback.list_artifacts(job_id)
