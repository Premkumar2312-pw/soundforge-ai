"""
Unit tests for Procedural Multi-Stem Synthesis, DSP, and Linear Reconstruction - PS1 Specification.
"""

import os
import shutil
import pytest
import numpy as np
import soundfile as sf
from soundforge.dsp.synthesis import ProceduralSynthesizer
from soundforge.dsp.mixer import mix_stems, DEFAULT_STEM_GAINS
from soundforge.dsp.music_theory import (
    calculate_sections,
    parse_key_signature,
    get_chord_progression
)
from soundforge.engine.generator import execute_generation_pipeline
from soundforge.models import MusicJobRequest

def test_genuine_multi_stem_synthesis():
    sr = 48000
    duration = 5.0
    synth = ProceduralSynthesizer(sample_rate=sr, seed=42)
    
    root_midi, mode = parse_key_signature("C_major")
    chord_progression = get_chord_progression(root_midi, mode)
    sections = calculate_sections(duration, None, bpm=120.0)
    
    stems = synth.render_all_stems(
        duration=duration,
        bpm=120.0,
        sections=sections,
        chord_progression=chord_progression,
        genre="electronic",
        loopability=False
    )
    
    expected_samples = int(duration * sr)
    assert set(stems.keys()) == {"drums", "bass", "chords", "melody"}
    
    for name, stem in stems.items():
        assert stem.shape == (expected_samples, 2), f"Stem {name} has incorrect shape: {stem.shape}"
        assert not np.isnan(stem).any(), f"Stem {name} contains NaN"
        assert not np.isinf(stem).any(), f"Stem {name} contains Inf"
        # Verify stem is not silent
        assert np.max(np.abs(stem)) > 0.01, f"Stem {name} is essentially silent"

    # Verify stems are genuinely independent instruments (not frequency-split copies)
    corr = np.corrcoef(stems["drums"][:, 0], stems["chords"][:, 0])[0, 1]
    assert abs(corr) < 0.5, f"Drums and chords have suspiciously high correlation {corr}"

def test_exact_linear_stem_reconstruction():
    sr = 48000
    duration = 5.0
    synth = ProceduralSynthesizer(sample_rate=sr, seed=99)
    root, mode = parse_key_signature("A_minor")
    chords = get_chord_progression(root, mode)
    sections = calculate_sections(duration, None, bpm=100.0)
    
    stems = synth.render_all_stems(duration, 100.0, sections, chords)
    mix, recon_error = mix_stems(stems, DEFAULT_STEM_GAINS)
    
    # Mathematical proof: Mix == sum(stem * gain)
    assert recon_error == 0.0
    manual_sum = (
        stems["drums"] * DEFAULT_STEM_GAINS["drums"] +
        stems["bass"] * DEFAULT_STEM_GAINS["bass"] +
        stems["chords"] * DEFAULT_STEM_GAINS["chords"] +
        stems["melody"] * DEFAULT_STEM_GAINS["melody"]
    )
    np.testing.assert_allclose(mix, manual_sum, atol=1e-7)

def test_deterministic_seed_reproducibility():
    sr = 48000
    duration = 5.0
    synth1 = ProceduralSynthesizer(sample_rate=sr, seed=777)
    synth2 = ProceduralSynthesizer(sample_rate=sr, seed=777)
    
    root, mode = parse_key_signature("G_major")
    chords = get_chord_progression(root, mode)
    sections = calculate_sections(duration, None, bpm=120.0)
    
    stems1 = synth1.render_all_stems(duration, 120.0, sections, chords)
    stems2 = synth2.render_all_stems(duration, 120.0, sections, chords)
    
    for k in stems1:
        np.testing.assert_array_equal(stems1[k], stems2[k], err_msg=f"Seed determinism failed for stem {k}")

@pytest.mark.asyncio
async def test_saved_disk_files_stem_reconstruction():
    """
    CRITICAL AUDIT TEST:
    Verify that saved mix.wav file on disk mathematically reconstructs from the
    saved stem_*.wav files on disk using the documented manifest gains.
    """
    temp_dir = "test_output/saved_recon_test"
    os.makedirs(temp_dir, exist_ok=True)
    try:
        req = MusicJobRequest(
            prompt="Electronic upbeat test track",
            duration=6.0,
            target_loudness=-16.0,
            output_formats=["wav"],
            seed=42
        )
        manifest = await execute_generation_pipeline("test-saved-recon", req, temp_dir)
        
        # Read saved audio files from disk
        mix_path = os.path.join(temp_dir, "mix.wav")
        assert os.path.exists(mix_path), "mix.wav was not created on disk"
        mix_audio, sr = sf.read(mix_path)
        assert sr == 48000, f"Expected 48000 Hz, got {sr}"
        
        stem_names = ["drums", "bass", "chords", "melody"]
        saved_stems = {}
        for name in stem_names:
            stem_path = os.path.join(temp_dir, f"stem_{name}.wav")
            assert os.path.exists(stem_path), f"stem_{name}.wav was not created on disk"
            stem_audio, stem_sr = sf.read(stem_path)
            assert stem_sr == 48000
            saved_stems[name] = stem_audio
            
        gains = manifest["stem_gains"]
        reconstructed = sum(saved_stems[name] * gains[name] for name in stem_names)
        
        # Exact disk reconstruction error check
        error = np.max(np.abs(mix_audio - reconstructed))
        assert error < 1e-5, f"Saved mix does not reconstruct from saved stems! Error: {error}"
        assert manifest["reconstruction_verification"]["perfect_reconstruction_verified"] is True
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
