"""
Local Filesystem Storage Provider for SoundForge AI
"""

import os
import shutil
from typing import List
from soundforge.storage.base import BaseStorageProvider
from soundforge.config import settings
from soundforge.utils.logging import logger

class LocalStorageProvider(BaseStorageProvider):
    def __init__(self, base_dir: str = None):
        self.base_dir = os.path.abspath(base_dir or settings.STORAGE_DIR)
        self.max_jobs = getattr(settings, "STORAGE_MAX_JOBS", 50)
        os.makedirs(self.base_dir, exist_ok=True)

    def prune_old_jobs(self, max_allowed: int = None):
        """Keep storage bounded to prevent disk exhaustion on long runs."""
        max_allowed = max_allowed or self.max_jobs
        try:
            entries = []
            for entry in os.scandir(self.base_dir):
                if entry.is_dir():
                    # Protect internal probe, upload cache and dotfiles
                    if entry.name.startswith(".") or entry.name.startswith("_"):
                        continue
                    try:
                        entries.append((entry.stat().st_mtime, entry.path))
                    except OSError:
                        pass

            if len(entries) > max_allowed:
                entries.sort(key=lambda x: x[0])  # Oldest first
                overflow = len(entries) - max_allowed
                for _, path in entries[:overflow]:
                    try:
                        shutil.rmtree(path, ignore_errors=True)
                    except Exception as ex:
                        logger.warning(f"Could not prune old storage dir {path}: {ex}")
        except Exception as e:
            logger.warning(f"Error checking storage bounds: {e}")

    def get_job_dir(self, job_id: str) -> str:
        self.prune_old_jobs()
        job_dir = os.path.join(self.base_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)
        return job_dir

    def get_artifact_path(self, job_id: str, filename: str) -> str:
        return os.path.join(self.get_job_dir(job_id), filename)

    def artifact_exists(self, job_id: str, filename: str) -> bool:
        path = self.get_artifact_path(job_id, filename)
        return os.path.exists(path)

    def list_artifacts(self, job_id: str) -> List[str]:
        job_dir = self.get_job_dir(job_id)
        if not os.path.exists(job_dir):
            return []
        return [f for f in os.listdir(job_dir) if os.path.isfile(os.path.join(job_dir, f))]
