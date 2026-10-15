"""
Unit tests for ITU-R BS.1770-4 / EBU R128 Loudness Normalization & True Peak Limiter.
"""

import pytest
import numpy as np
from soundforge.dsp.mastering import master_audio, measure_audio_metrics

def test_mastering_loudness_targeting():
    sr = 48000
    duration = 5.0
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    # Generate test audio signal (stereo multi-tone)
    test_sig = np.column_stack((
        0.3 * np.sin(2 * np.pi * 220 * t) + 0.2 * np.sin(2 * np.pi * 440 * t),
        0.3 * np.sin(2 * np.pi * 330 * t) + 0.2 * np.sin(2 * np.pi * 660 * t)
    )).astype(np.float32)

    # Test normalization to -14.0 LUFS
    mastered, report = master_audio(test_sig, target_loudness_lufs=-14.0, max_true_peak_dbtp=-1.0, sample_rate=sr)
    
    assert abs(report["final_loudness_lufs"] - (-14.0)) < 0.6, f"Loudness deviation too high: {report['final_loudness_lufs']}"
    assert report["final_true_peak_dbtp"] <= -0.9, f"Peak exceeds -1.0 dBTP limit: {report['final_true_peak_dbtp']}"
    assert not np.isnan(mastered).any()

def test_mastering_high_peak_limiting():
    sr = 48000
    duration = 2.0
    t = np.linspace(0, duration, int(duration * sr), endpoint=False)
    # Excessive signal with peaks reaching +6 dBFS
    loud_sig = (2.0 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    loud_sig = np.column_stack((loud_sig, loud_sig))

    mastered, report = master_audio(loud_sig, target_loudness_lufs=-14.0, max_true_peak_dbtp=-1.0, sample_rate=sr)
    
    peak_linear = np.max(np.abs(mastered))
    assert peak_linear <= 10.0 ** (-1.0 / 20.0) + 1e-4
    assert report["final_true_peak_dbtp"] <= -0.95
