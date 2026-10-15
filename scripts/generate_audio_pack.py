"""
Generate a Demonstration Audio Pack for SoundForge AI
Creates reference WAV, MP3, Stems, and Manifest files for technical review.
"""

import os
import sys
import asyncio

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from soundforge.models import MusicJobRequest, MusicalSection
from soundforge.engine.generator import execute_generation_pipeline

DEMO_PACKS = [
    {
        "folder": "demo_audio_pack/01_corporate_upbeat",
        "request": MusicJobRequest(
            prompt="Upbeat modern corporate tech explainer music with inspiring synth melody",
            duration=12.0,
            tempo=120.0,
            key="C_major",
            loopability=False,
            target_loudness=-16.0,
            output_formats=["wav", "mp3"],
            seed=101
        )
    },
    {
        "folder": "demo_audio_pack/02_lofi_chill_loop",
        "request": MusicJobRequest(
            prompt="Chill lo-fi study beat with mellow electric piano and warm bassline",
            duration=16.0,
            tempo=82.0,
            key="A_minor",
            loopability=True,
            target_loudness=-16.0,
            output_formats=["wav", "mp3"],
            seed=202
        )
    },
    {
        "folder": "demo_audio_pack/03_cinematic_trailer",
        "request": MusicJobRequest(
            prompt="Cinematic dramatic trailer intro with rising tension and pounding drums",
            duration=14.0,
            tempo=94.0,
            key="D_minor",
            sections=[
                MusicalSection(name="intro_drone", duration=3.0),
                MusicalSection(name="tension_build", duration=6.0),
                MusicalSection(name="climax_drop", duration=5.0)
            ],
            loopability=False,
            target_loudness=-16.0,
            output_formats=["wav", "mp3"],
            seed=303
        )
    }
]

async def main():
    print("Generating SoundForge AI Reference Audio Pack...")
    for pack in DEMO_PACKS:
        folder = pack["folder"]
        req = pack["request"]
        print(f"\n[+] Generating {folder} (Duration: {req.duration}s, BPM: {req.tempo})...")
        manifest = await execute_generation_pipeline(
            job_id=os.path.basename(folder),
            request=req,
            output_dir=folder
        )
        print(f"    Mix: {folder}/mix.wav")
        print(f"    LUFS: {manifest['audio_metrics']['measured_loudness_lufs']}")
        print(f"    True Peak: {manifest['audio_metrics']['true_peak_dbtp']} dBTP")
        print(f"    Reconstruction Error: {manifest['reconstruction_verification']['max_reconstruction_error']}")
    print("\n[V] Audio pack successfully generated in 'demo_audio_pack/'!")

if __name__ == "__main__":
    asyncio.run(main())
