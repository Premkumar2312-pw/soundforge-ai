"""
Storage factory for SoundForge AI
"""

from soundforge.config import settings
from soundforge.storage.base import BaseStorageProvider
from soundforge.storage.local import LocalStorageProvider
from soundforge.storage.s3 import S3StorageProvider

def get_storage_provider() -> BaseStorageProvider:
    if settings.STORAGE_BACKEND.lower() == "s3":
        return S3StorageProvider()
    return LocalStorageProvider()
