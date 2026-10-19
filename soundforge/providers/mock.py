"""
Deterministic Mock Provider for SoundForge AI
Enables instant zero-compute testing, CI pipelines, and error/timeout simulation.
"""

import os
import json
import time
import asyncio
import numpy as np
import soundfile as sf
from typing import Dict, Any, Callable, Optional

from soundforge.providers.base import BaseMusicProvider
from soundforge.models import MusicJobRequest, MusicalSection
from soundforge.dsp.mixer import DEFAULT_STEM_GAINS
from soundforge.manifest import build_manifest

class MockDeterministicProvider(BaseMusicProvider):
    """
    Deterministic mock provider for high-speed offline testing.
    Produces valid 48 kHz 24-bit PCM WAV and manifest files instantly.
    """

    async def generate(
        self,
        job_id: str,
        request: MusicJobRequest,
        output_dir: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        # Error simulation for Hard Case #15
        if "__SIMULATE_FAILURE__" in request.prompt:
            raise RuntimeError("Simulated provider failure triggered by test harness.")
        if "__SIMULATE_TIMEOUT__" in request.prompt:
            await asyncio.sleep(5.0)
            raise TimeoutError("Simulated provider timeout exceeded.")

        if progress_callback:
            progress_callback(0.1, "Mock: Initializing")

        os.makedirs(output_dir, exist_ok=True)
        stems_dir = os.path.join(output_dir, "stems")
        os.makedirs(stems_dir, exist_ok=True)

        sr = request.sample_rate
        total_samples = int(round(request.duration * sr))
        t = np.linspace(0, request.duration, total_samples, endpoint=False)

        # Generate simple distinct harmonic tones for 4 stems
        stem_freqs = {"drums": 60.0, "bass": 110.0, "chords": 440.0, "melody": 880.0}
        stems = {}
        for name, freq in stem_freqs.items():
            tone = (np.sin(2.0 * np.pi * freq * t) * 0.2).astype(np.float32)
            stems[name] = np.column_stack((tone, tone))

        if progress_callback:
            progress_callback(0.5, "Mock: Synthesized stems")

        # Mix stems
        mix = np.zeros((total_samples, 2), dtype=np.float32)
        for name, audio in stems.items():
            mix += audio * DEFAULT_STEM_GAINS[name]

        # Write stems (both root and stems/)
        for name, audio in stems.items():
            sf.write(os.path.join(output_dir, f"stem_{name}.wav"), audio, sr, subtype='PCM_24')
            sf.write(os.path.join(stems_dir, f"{name}.wav"), audio, sr, subtype='PCM_24')

        # Write mix
        sf.write(os.path.join(output_dir, "mix.wav"), mix, sr, subtype='PCM_24')

        if "mp3" in [f.lower() for f in request.output_formats]:
            try:
                sf.write(os.path.join(output_dir, "mix.mp3"), mix, sr, format='MP3')
            except Exception:
                pass

        if progress_callback:
            progress_callback(0.9, "Mock: Finalizing manifest")

        sections = [
            MusicalSection(name="intro", duration=request.duration * 0.3, start_time=0.0, end_time=request.duration * 0.3),
            MusicalSection(name="outro", duration=request.duration * 0.7, start_time=request.duration * 0.3, end_time=request.duration)
        ]

        mastering_report = {
            "target_loudness_lufs": request.target_loudness,
            "final_loudness_lufs": request.target_loudness,
            "final_true_peak_dbtp": -1.0,
            "max_true_peak_limit_dbtp": -1.0,
            "gain_applied_db": 0.0
        }

        manifest = build_manifest(
            job_id=job_id,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            prompt=request.prompt,
            target_duration=request.duration,
            actual_duration=request.duration,
            sample_rate=sr,
            tempo=120.0,
            key=request.key or "C_major",
            genre="mock",
            sections=sections,
            stem_gains=DEFAULT_STEM_GAINS,
            max_recon_error=0.0,
            mastering_report=mastering_report,
            ducking_report=None,
            output_formats=request.output_formats,
            seed=request.seed or 42,
            loopability=request.loopability,
            timings_ms={"total_pipeline_time_ms": 25.0},
            warnings=[]
        )

        for fname in ["music_manifest.json", "manifest.json"]:
            with open(os.path.join(output_dir, fname), "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

        if progress_callback:
            progress_callback(1.0, "Mock: Completed")

        return manifest
