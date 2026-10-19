"""
Procedural DSP Music Provider for SoundForge AI
Wraps the real procedural DSP synthesis engine.
Zero external API keys, zero paid services, 100% commercially cleared procedural generation.
"""

from typing import Dict, Any, Callable, Optional
from soundforge.providers.base import BaseMusicProvider
from soundforge.models import MusicJobRequest
from soundforge.engine.generator import execute_generation_pipeline

class ProceduralDSPProvider(BaseMusicProvider):
    """
    Primary real generation engine for SoundForge AI.
    Generates genuine multi-stem procedural audio via DSP algorithms.
    """

    async def generate(
        self,
        job_id: str,
        request: MusicJobRequest,
        output_dir: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        return await execute_generation_pipeline(
            job_id=job_id,
            request=request,
            output_dir=output_dir,
            progress_callback=progress_callback
        )
