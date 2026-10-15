"""
Unit tests for PS1 Manifest Specification Compliance.
"""

import pytest
from soundforge.models import MusicalSection
from soundforge.manifest import build_manifest

def test_manifest_schema_completeness():
    sections = [
        MusicalSection(name="intro", duration=2.0, start_time=0.0, end_time=2.0, start_bar=0, end_bar=1),
        MusicalSection(name="main", duration=4.0, start_time=2.0, end_time=6.0, start_bar=1, end_bar=3)
    ]
    stem_gains = {"drums": 0.85, "bass": 0.80, "chords": 0.70, "melody": 0.75}
    mastering_report = {
        "target_loudness_lufs": -16.0,
        "final_loudness_lufs": -16.02,
        "final_true_peak_dbtp": -1.05,
        "max_true_peak_limit_dbtp": -1.0,
        "gain_applied_db": 1.2
    }
    timings = {
        "generation_time_ms": 120.0,
        "mixing_time_ms": 10.0,
        "mastering_time_ms": 15.0,
        "ducking_time_ms": 0.0,
        "total_pipeline_time_ms": 145.0
    }
    
    manifest = build_manifest(
        job_id="test-job-uuid",
        created_at="2026-10-15T12:00:00Z",
        prompt="Lo-fi hip hop chill beats",
        target_duration=6.0,
        actual_duration=6.0,
        sample_rate=48000,
        tempo=84.0,
        key="A_minor",
        genre="lofi",
        sections=sections,
        stem_gains=stem_gains,
        max_recon_error=0.0,
        mastering_report=mastering_report,
        ducking_report=None,
        output_formats=["wav", "mp3"],
        seed=42,
        loopability=True,
        timings_ms=timings,
        warnings=[]
    )
    
    # Required top-level keys
    required_keys = [
        "manifest_version", "job_id", "created_at", "completed_at", "status",
        "request_parameters", "musical_settings", "sections", "beat_bar_timing",
        "stem_gains", "reconstruction_verification", "audio_metrics",
        "ducking", "provenance", "timings_ms", "cost_estimates", "artifacts", "warnings"
    ]
    for k in required_keys:
        assert k in manifest, f"Missing required manifest key: {k}"

    assert manifest["reconstruction_verification"]["perfect_reconstruction_verified"] is True
    assert manifest["provenance"]["commercial_cleared"] is True
    assert "soundforge_engine" in manifest["provenance"]["component_licenses"]
    assert len(manifest["sections"]) == 2
    assert manifest["audio_metrics"]["channels"] == 2
    assert manifest["audio_metrics"]["sample_rate_hz"] == 48000
