"""
Music Generation Pipeline Orchestrator for SoundForge AI
Coordinates theory analysis, multi-stem synthesis, mixing, mastering, ducking, validation, and serialization.
"""

import os
import time
import json
import numpy as np
import soundfile as sf
from typing import Dict, Any, Callable, Optional

from soundforge.models import MusicJobRequest
from soundforge.dsp.music_theory import (
    analyze_prompt_musicality,
    parse_key_signature,
    get_chord_progression,
    calculate_sections
)
from soundforge.dsp.synthesis import ProceduralSynthesizer
from soundforge.dsp.mixer import mix_stems, DEFAULT_STEM_GAINS
from soundforge.dsp.mastering import master_audio
from soundforge.dsp.ducking import load_narration_audio, apply_sidechain_ducking
from soundforge.dsp.validator import validate_audio_file
from soundforge.manifest import build_manifest
from soundforge.utils.logging import logger

async def execute_generation_pipeline(
    job_id: str,
    request: MusicJobRequest,
    output_dir: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Dict[str, Any]:
    """
    Run complete end-to-end music generation job.
    """
    pipeline_start = time.perf_counter()
    timings: Dict[str, float] = {}
    warnings: list[str] = []
    
    os.makedirs(output_dir, exist_ok=True)
    
    def update_progress(progress: float, stage: str):
        if progress_callback:
            progress_callback(progress, stage)
        logger.info(f"[{job_id}] Progress {int(progress * 100)}%: {stage}", extra={"job_id": job_id})
        
    update_progress(0.05, "Analyzing prompt and musical parameters")
    
    # 1. Analyze prompt and musical parameters
    prompt_meta = analyze_prompt_musicality(request.prompt)
    tempo = request.tempo if request.tempo is not None else prompt_meta["bpm"]
    key_str = request.key if request.key is not None else prompt_meta["key"]
    genre = prompt_meta["genre"]
    seed = request.seed if request.seed is not None else int(time.time() * 1000) % 100000000
    
    root_midi, mode = parse_key_signature(key_str)
    chord_progression = get_chord_progression(root_midi, mode)
    sections = calculate_sections(request.duration, request.sections, tempo)
    
    # 2. Synthesize Multi-Track Stems
    update_progress(0.20, "Synthesizing 4 genuine instrument stems")
    t0 = time.perf_counter()
    synth = ProceduralSynthesizer(sample_rate=request.sample_rate, seed=seed)
    stems = synth.render_all_stems(
        duration=request.duration,
        bpm=tempo,
        sections=sections,
        chord_progression=chord_progression,
        genre=genre,
        loopability=request.loopability
    )
    timings["generation_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    
    # 3. Linear Stem Mixing
    update_progress(0.50, "Performing linear stem mix and reconstruction verification")
    t0 = time.perf_counter()
    raw_mix, max_recon_error = mix_stems(stems, DEFAULT_STEM_GAINS)
    timings["mixing_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    
    # 4. Mastering & Loudness Normalization
    update_progress(0.65, "Mastering, EBU R128 loudness normalization and True Peak limiting")
    t0 = time.perf_counter()
    mastered_mix, mastering_report = master_audio(
        raw_mix,
        target_loudness_lufs=request.target_loudness,
        max_true_peak_dbtp=-1.0,
        sample_rate=request.sample_rate
    )
    timings["mastering_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    
    # 5. Sidechain Narration Ducking (if narration supplied)
    ducking_report = None
    ducked_mix = None
    if request.narration_url:
        update_progress(0.75, "Applying sidechain narration ducking")
        t0 = time.perf_counter()
        try:
            narration_audio = await load_narration_audio(request.narration_url, target_sr=request.sample_rate)
            ducked_mix, ducking_report = apply_sidechain_ducking(
                mastered_mix,
                narration_audio,
                sample_rate=request.sample_rate
            )
        except Exception as e:
            logger.warning(f"Failed to load or apply narration ducking: {e}", extra={"job_id": job_id})
            warnings.append(f"Narration ducking could not be applied: {str(e)}")
            ducking_report = {"ducking_applied": False, "error": str(e)}
        timings["ducking_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    else:
        timings["ducking_time_ms"] = 0.0
        
    # 6. Audio Validation
    update_progress(0.85, "Validating audio delivery specifications")
    val_result = validate_audio_file(
        mastered_mix,
        target_duration=request.duration,
        sample_rate=request.sample_rate,
        expected_channels=2
    )
    if val_result["warnings"]:
        warnings.extend(val_result["warnings"])
    if not val_result["valid"]:
        raise ValueError(f"Audio validation failed: {', '.join(val_result['errors'])}")
        
    # 7. Write Audio Artifacts
    update_progress(0.90, "Writing audio files (WAV, MP3) and stems")
    
    # Stems
    for stem_name, stem_audio in stems.items():
        sf.write(os.path.join(output_dir, f"stem_{stem_name}.wav"), stem_audio, request.sample_rate, subtype='PCM_24')
        
    # Master mix WAV (48 kHz 24-bit PCM)
    mix_wav_path = os.path.join(output_dir, "mix.wav")
    sf.write(mix_wav_path, mastered_mix, request.sample_rate, subtype='PCM_24')
    
    # MP3 if requested
    if "mp3" in [f.lower() for f in request.output_formats]:
        mix_mp3_path = os.path.join(output_dir, "mix.mp3")
        sf.write(mix_mp3_path, mastered_mix, request.sample_rate, format='MP3')
        
    # Ducked mix if generated
    if ducked_mix is not None:
        ducked_wav_path = os.path.join(output_dir, "ducked_mix.wav")
        sf.write(ducked_wav_path, ducked_mix, request.sample_rate, subtype='PCM_24')
        
    actual_duration = len(mastered_mix) / request.sample_rate
    timings["total_pipeline_time_ms"] = round((time.perf_counter() - pipeline_start) * 1000, 2)
    
    # 8. Build Manifest
    update_progress(0.98, "Generating manifest")
    manifest = build_manifest(
        job_id=job_id,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        prompt=request.prompt,
        target_duration=request.duration,
        actual_duration=actual_duration,
        sample_rate=request.sample_rate,
        tempo=tempo,
        key=key_str,
        genre=genre,
        sections=sections,
        stem_gains=DEFAULT_STEM_GAINS,
        max_recon_error=max_recon_error,
        mastering_report=mastering_report,
        ducking_report=ducking_report,
        output_formats=request.output_formats,
        seed=seed,
        loopability=request.loopability,
        timings_ms=timings,
        warnings=warnings
    )
    
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    update_progress(1.0, "Generation completed successfully")
    return manifest
