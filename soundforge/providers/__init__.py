"""
Provider Factory for SoundForge AI
Selects active generation provider based on environment configuration.
"""

from typing import Optional
from soundforge.config import settings
from soundforge.providers.base import BaseMusicProvider
from soundforge.providers.procedural import ProceduralDSPProvider
from soundforge.providers.mock import MockDeterministicProvider

def get_provider(provider_name: Optional[str] = None) -> BaseMusicProvider:
    """
    Return provider instance based on name or configuration setting.
    Supported: 'procedural' (default), 'mock'.
    """
    name = (provider_name or settings.PROVIDER).lower()
    if name == "mock":
        return MockDeterministicProvider()
    elif name == "procedural":
        return ProceduralDSPProvider()
    else:
        raise ValueError(f"Unknown music provider '{name}'. Supported: ['procedural', 'mock']")
