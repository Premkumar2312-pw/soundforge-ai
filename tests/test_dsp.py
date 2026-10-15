"""
Unit tests for Procedural Multi-Stem Synthesis, DSP, and Linear Reconstruction.
"""

import pytest
import numpy as np
from soundforge.dsp.synthesis import ProceduralSynthesizer
from soundforge.dsp.mixer import mix_stems, DEFAULT_STEM_GAINS
from soundforge.dsp.music_theory import (
    calculate_sections,
    parse_key_signature,
    get_chord_progression
)

def test_genuine_multi_stem_synthesis():
    sr = 48000
    duration = 4.0
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
    # Correlation between drums and chords should be low
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
    duration = 3.0
    synth1 = ProceduralSynthesizer(sample_rate=sr, seed=777)
    synth2 = ProceduralSynthesizer(sample_rate=sr, seed=777)
    
    root, mode = parse_key_signature("G_major")
    chords = get_chord_progression(root, mode)
    sections = calculate_sections(duration, None, bpm=120.0)
    
    stems1 = synth1.render_all_stems(duration, 120.0, sections, chords)
    stems2 = synth2.render_all_stems(duration, 120.0, sections, chords)
    
    for k in stems1:
        np.testing.assert_array_equal(stems1[k], stems2[k], err_msg=f"Seed determinism failed for stem {k}")
