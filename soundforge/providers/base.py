"""
Base Music Provider Interface for SoundForge AI
Abstract Base Class defining the contract for music generation providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional
from soundforge.models import MusicJobRequest

class BaseMusicProvider(ABC):
    """Abstract interface for SoundForge AI generation engines."""

    @abstractmethod
    async def generate(
        self,
        job_id: str,
        request: MusicJobRequest,
        output_dir: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Execute generation pipeline and return manifest dictionary.
        Must write mix.wav, stems, and manifest to output_dir.
        """
        pass
