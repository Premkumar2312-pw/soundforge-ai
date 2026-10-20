"""
Automated Prompt Diversity and Audio Feature Contrast Tests for SoundForge AI
Verifies that distinct prompt directions (Ambient, Dance, Acoustic, Tense, Lo-Fi, Cinematic)
generate genuinely different audio compositions in timbre, spectral balance, rhythmic density,
and musical structure, rather than superficial variations or identical audio.
"""

import pytest
import numpy as np
import scipy.signal as signal
from soundforge.dsp.music_theory import analyze_prompt_musicality, parse_key_signature, get_chord_progression, calculate_sections
from soundforge.dsp.synthesis import ProceduralSynthesizer
from soundforge.dsp.mixer import mix_stems, DEFAULT_STEM_GAINS

def compute_spectral_centroid(audio: np.ndarray, sr: int = 48000) -> float:
    """Calculate the spectral centroid (center of mass of spectrum / perceived brightness)."""
    mono = np.mean(audio, axis=1) if audio.ndim > 1 else audio
    spectrum = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(len(mono), d=1.0/sr)
    sum_spec = np.sum(spectrum)
    if sum_spec < 1e-9:
        return 0.0
    return float(np.sum(freqs * spectrum) / sum_spec)

def compute_zero_crossing_rate(audio: np.ndarray) -> float:
    """Calculate normalized zero-crossing rate (percussive/transient density)."""
    mono = np.mean(audio, axis=1) if audio.ndim > 1 else audio
    zero_crossings = np.sum(np.abs(np.diff(np.signbit(mono))))
    return float(zero_crossings / len(mono))

def compute_drum_onset_energy(stem_drums: np.ndarray, sr: int = 48000) -> float:
    """Compute high-frequency transient energy in the drums stem."""
    mono = np.mean(stem_drums, axis=1) if stem_drums.ndim > 1 else stem_drums
    # High-pass filter above 2.5 kHz to isolate snare/hat transients
    sos = signal.butter(2, 2500.0, btype='highpass', fs=sr, output='sos')
    hf = signal.sosfilt(sos, mono)
    return float(np.mean(hf ** 2) * 1e4)

def synthesize_for_prompt(prompt: str, duration: float = 6.0, seed: int = 101):
    sr = 48000
    meta = analyze_prompt_musicality(prompt)
    root_midi, mode = parse_key_signature(meta["key"])
    chords = get_chord_progression(root_midi, mode, genre=meta["genre"])
    sections = calculate_sections(duration, None, bpm=meta["bpm"])
    synth = ProceduralSynthesizer(sample_rate=sr, seed=seed)
    stems = synth.render_all_stems(
        duration=duration,
        bpm=meta["bpm"],
        sections=sections,
        chord_progression=chords,
        genre=meta["genre"],
        energy=meta["energy"],
        loopability=False
    )
    mix, _ = mix_stems(stems, DEFAULT_STEM_GAINS)
    return {
        "genre": meta["genre"],
        "bpm": meta["bpm"],
        "stems": stems,
        "mix": mix,
        "centroid": compute_spectral_centroid(mix, sr),
        "zcr": compute_zero_crossing_rate(mix),
        "drum_energy": compute_drum_onset_energy(stems["drums"], sr)
    }

def test_ambient_vs_dance_audio_contrast():
    """Ambient meditation drone vs energetic club dance must exhibit massive spectral and rhythmic contrast."""
    ambient = synthesize_for_prompt("Serene peaceful ambient meditation drone with calm stillness", duration=6.0, seed=101)
    dance = synthesize_for_prompt("High energy electronic dance track with driving four on the floor beat", duration=6.0, seed=101)

    # 1. Dance must have dramatically higher tempo than ambient
    assert dance["bpm"] >= 120.0
    assert ambient["bpm"] <= 70.0

    # 2. Dance must have far higher drum transient energy than ambient drone
    assert dance["drum_energy"] > ambient["drum_energy"] * 2.5, (
        f"Dance drum energy ({dance['drum_energy']:.3f}) should be > 2.5x ambient ({ambient['drum_energy']:.3f})"
    )

    # 3. Waveforms must have substantial divergence (correlation < 0.2)
    m_amb = np.mean(ambient["mix"], axis=1)
    m_dnc = np.mean(dance["mix"], axis=1)
    corr = float(np.abs(np.corrcoef(m_amb, m_dnc)[0, 1]))
    assert corr < 0.20, f"Ambient and Dance should have near-zero correlation, got {corr:.3f}"

def test_acoustic_folk_vs_tense_thriller_contrast():
    """Acoustic folk strumming vs tense crime thriller underscore."""
    folk = synthesize_for_prompt("Warm organic acoustic folk melody with gentle guitar strumming", duration=6.0, seed=102)
    tense = synthesize_for_prompt("Dark suspense crime thriller underscore with nervous ticking", duration=6.0, seed=102)

    # Folk uses plucked acoustic guitar and upright bass
    # Tense uses clock ticks and dissonant minor second clusters
    assert folk["genre"] == "acoustic"
    assert tense["genre"] == "tense"

    # Spectral centroids must be distinctly separated
    assert abs(folk["centroid"] - tense["centroid"]) > 100.0

    # Cross-correlation between mixes must be low
    m_flk = np.mean(folk["mix"], axis=1)
    m_tns = np.mean(tense["mix"], axis=1)
    corr = float(np.abs(np.corrcoef(m_flk, m_tns)[0, 1]))
    assert corr < 0.25, f"Folk and Tense should not correlate, got {corr:.3f}"

def test_lofi_vs_corporate_audio_contrast():
    """Warm muffled lo-fi study beat vs bright crisp corporate tech tutorial."""
    lofi = synthesize_for_prompt("Relaxing lo-fi chill study beat with soft electric piano Rhodes", duration=6.0, seed=103)
    corp = synthesize_for_prompt("Modern corporate tech presentation with bright optimistic marimba", duration=6.0, seed=103)

    assert lofi["genre"] == "lofi"
    assert corp["genre"] == "corporate"

    # Corporate with bright bells and crisp hats has higher spectral centroid than warm muffled lofi
    assert corp["centroid"] > lofi["centroid"] * 1.15, (
        f"Corporate brightness ({corp['centroid']:.1f}Hz) must exceed LoFi ({lofi['centroid']:.1f}Hz) by >= 15%"
    )

    # Drum onset energy differs due to crisp snap vs soft rimshot
    assert corp["drum_energy"] > lofi["drum_energy"]

def test_cinematic_epic_percussion_scale():
    """Cinematic orchestral build features massive taiko sub-boom and brass swells."""
    cine = synthesize_for_prompt("Epic dramatic orchestral movie trailer intro with heroic brass climax", duration=6.0, seed=104)
    assert cine["genre"] == "cinematic"

    # Verify drums contain significant low sub energy (below 80 Hz) from the taiko boom
    drum_mono = np.mean(cine["stems"]["drums"], axis=1)
    sos = signal.butter(2, 80.0, btype='lowpass', fs=48000, output='sos')
    sub_energy = float(np.mean(signal.sosfilt(sos, drum_mono) ** 2))
    assert sub_energy > 0.001, "Cinematic taiko boom must have substantial sub-80Hz body"

def test_deterministic_reproducibility_per_prompt():
    """Same prompt and same seed always produces bit-for-bit identical stems across all genres."""
    run1 = synthesize_for_prompt("Quirky playful comedy video game music", duration=5.0, seed=777)
    run2 = synthesize_for_prompt("Quirky playful comedy video game music", duration=5.0, seed=777)

    for k in ["drums", "bass", "chords", "melody"]:
        np.testing.assert_array_equal(run1["stems"][k], run2["stems"][k])
    np.testing.assert_array_equal(run1["mix"], run2["mix"])
