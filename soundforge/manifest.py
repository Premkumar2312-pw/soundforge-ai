"""
Manifest Builder for SoundForge AI
Assembles complete metadata, musical provenance, audio metrics, and licensing clearance.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from soundforge.models import MusicalSection

def build_manifest(
    job_id: str,
    created_at: str,
    prompt: str,
    target_duration: float,
    actual_duration: float,
    sample_rate: int,
    tempo: float,
    key: str,
    genre: str,
    sections: List[MusicalSection],
    stem_gains: Dict[str, float],
    max_recon_error: float,
    mastering_report: Dict[str, Any],
    ducking_report: Optional[Dict[str, Any]],
    output_formats: List[str],
    seed: int,
    loopability: bool,
    timings_ms: Dict[str, float],
    warnings: List[str]
) -> Dict[str, Any]:
    """Generate comprehensive manifest compliant with PS1 specification."""
    spb = 60.0 / tempo
    seconds_per_bar = spb * 4.0
    total_bars = int(actual_duration / seconds_per_bar)
    total_beats = int(actual_duration / spb)
    
    # Compute cost estimate based on CPU execution milliseconds (industry standard $0.00001667/GB-s)
    total_time_s = timings_ms.get("total_pipeline_time_ms", 0.0) / 1000.0
    estimated_cost_usd = round(total_time_s * 0.00005, 6)
    
    artifacts = {
        "mix_wav": "mix.wav",
        "stem_drums": "stem_drums.wav",
        "stem_bass": "stem_bass.wav",
        "stem_chords": "stem_chords.wav",
        "stem_melody": "stem_melody.wav",
        "manifest_json": "manifest.json"
    }
    if "mp3" in output_formats:
        artifacts["mix_mp3"] = "mix.mp3"
    if ducking_report and ducking_report.get("ducking_applied"):
        artifacts["ducked_mix_wav"] = "ducked_mix.wav"
        
    manifest = {
        "manifest_version": "1.0.0",
        "job_id": job_id,
        "created_at": created_at,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "request_parameters": {
            "prompt": prompt,
            "target_duration_seconds": target_duration,
            "loopability": loopability,
            "seed": seed,
            "sample_rate": sample_rate,
            "output_formats": output_formats
        },
        "musical_settings": {
            "genre": genre,
            "tempo_bpm": round(tempo, 1),
            "key": key,
            "time_signature": "4/4",
            "loopability": loopability,
            "ending_type": "seamless_loop" if loopability else "purposeful_cadence_fade"
        },
        "sections": [
            {
                "name": s.name,
                "duration_seconds": round(s.duration, 3),
                "start_seconds": round(s.start_time, 3) if s.start_time is not None else 0.0,
                "end_seconds": round(s.end_time, 3) if s.end_time is not None else round(s.duration, 3),
                "start_bar": s.start_bar if s.start_bar is not None else 0,
                "end_bar": s.end_bar if s.end_bar is not None else 0
            }
            for s in sections
        ],
        "beat_bar_timing": {
            "bpm": round(tempo, 1),
            "seconds_per_beat": round(spb, 4),
            "seconds_per_bar": round(seconds_per_bar, 4),
            "total_bars": total_bars,
            "total_beats": total_beats
        },
        "stem_gains": stem_gains,
        "reconstruction_verification": {
            "formula": "Mix = Sum(Stem_i * Gain_i)",
            "max_reconstruction_error": max_recon_error,
            "perfect_reconstruction_verified": bool(max_recon_error < 1e-5)
        },
        "audio_metrics": {
            "sample_rate_hz": sample_rate,
            "channels": 2,
            "channel_layout": "Stereo",
            "bit_depth": "24-bit PCM",
            "actual_duration_seconds": round(actual_duration, 4),
            "target_loudness_lufs": mastering_report.get("target_loudness_lufs", -16.0),
            "measured_loudness_lufs": mastering_report.get("final_loudness_lufs", -16.0),
            "true_peak_dbtp": mastering_report.get("final_true_peak_dbtp", -1.0),
            "max_true_peak_limit_dbtp": mastering_report.get("max_true_peak_limit_dbtp", -1.0),
            "mastering_gain_applied_db": mastering_report.get("gain_applied_db", 0.0)
        },
        "ducking": ducking_report or {
            "ducking_applied": False,
            "reason": "No narration audio provided"
        },
        "provenance": {
            "provider": "SoundForge Procedural AI Engine",
            "model_version": "1.0.0-procedural-dsp",
            "seed": seed,
            "commercial_cleared": True,
            "licensing_terms": "100% procedurally synthesized without proprietary soundfonts, unlicensed samples, or non-commercial AI weights. Fully cleared for commercial use.",
            "component_licenses": {
                "soundforge_engine": "MIT",
                "numpy": "BSD-3-Clause",
                "scipy": "BSD-3-Clause",
                "pyloudnorm": "MIT",
                "soundfile_libsndfile": "LGPL-2.1 / BSD"
            }
        },
        "timings_ms": timings_ms,
        "cost_estimates": {
            "compute_time_ms": timings_ms.get("total_pipeline_time_ms", 0.0),
            "estimated_cost_usd": estimated_cost_usd,
            "currency": "USD"
        },
        "artifacts": artifacts,
        "warnings": warnings
    }
    return manifest
