"""
Storage Provider Abstract Base Class for SoundForge AI
"""

from abc import ABC, abstractmethod
from typing import List, Optional

class BaseStorageProvider(ABC):
    @abstractmethod
    def get_job_dir(self, job_id: str) -> str:
        """Get absolute path or URI to the job's directory."""
        pass

    @abstractmethod
    def get_artifact_path(self, job_id: str, filename: str) -> str:
        """Get path to a specific artifact."""
        pass

    @abstractmethod
    def artifact_exists(self, job_id: str, filename: str) -> bool:
        """Check if artifact exists."""
        pass

    @abstractmethod
    def list_artifacts(self, job_id: str) -> List[str]:
        """List filenames of all artifacts for a job."""
        pass
