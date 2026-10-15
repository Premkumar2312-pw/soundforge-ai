"""
Unit tests for Sidechain Narration Ducking Compressor.
"""

import pytest
import numpy as np
from soundforge.dsp.ducking import apply_sidechain_ducking

def test_sidechain_ducking_attenuation():
    sr = 48000
    duration = 4.0
    total_samples = int(duration * sr)
    t = np.linspace(0, duration, total_samples, endpoint=False)
    
    # Constant 440 Hz instrumental music bed
    music_bed = 0.5 * np.sin(2 * np.pi * 440 * t)
    instrumental = np.column_stack((music_bed, music_bed)).astype(np.float32)
    
    # Narration voice: silence for 1s, speech for 2s (1s to 3s), silence for 1s
    narration = np.zeros((total_samples, 2), dtype=np.float32)
    speech_start = int(1.0 * sr)
    speech_end = int(3.0 * sr)
    narration[speech_start:speech_end, :] = 0.6 * np.sin(2 * np.pi * 800 * t[speech_start:speech_end, None])
    
    ducked, metrics = apply_sidechain_ducking(
        instrumental=instrumental,
        narration=narration,
        sample_rate=sr,
        ducking_attenuation_db=-12.0
    )
    
    assert metrics["ducking_applied"] is True
    assert metrics["speech_activity_seconds"] > 1.5
    
    # Check peak level in a window during silence (0.4s to 0.6s) - should be full volume (~0.5)
    silence_window = ducked[int(0.4 * sr):int(0.6 * sr), 0]
    level_before_speech = np.max(np.abs(silence_window))
    assert level_before_speech > 0.45
    
    # Check peak level in a window during speech (1.8s to 2.2s) - should be ducked by ~ -12 dB (factor ~0.25)
    speech_window = ducked[int(1.8 * sr):int(2.2 * sr), 0]
    level_during_speech = np.max(np.abs(speech_window))
    assert level_during_speech < 0.20
    assert level_during_speech < level_before_speech * 0.45
