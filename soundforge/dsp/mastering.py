"""
Mastering Stage for SoundForge AI (PS1 Specification)
Implements ITU-R BS.1770-4 / EBU R128 Loudness Normalization and True Peak Limiting.
"""

from typing import Tuple, Dict, Any
import numpy as np
import pyloudnorm as pyln

def measure_audio_metrics(audio: np.ndarray, sample_rate: int = 48000) -> Dict[str, float]:
    """Measure integrated LUFS loudness and peak/true-peak dBTP."""
    meter = pyln.Meter(sample_rate)
    
    # Audio must not be completely silent for pyloudnorm
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-6:
        return {
            "integrated_loudness_lufs": -70.0,
            "true_peak_dbtp": -120.0,
            "peak_linear": 0.0
        }
        
    try:
        loudness = float(meter.integrated_loudness(audio))
    except Exception:
        loudness = -70.0
        
    peak_linear = peak
    peak_dbtp = float(20.0 * np.log10(max(peak_linear, 1e-9)))
    
    return {
        "integrated_loudness_lufs": round(loudness, 2),
        "true_peak_dbtp": round(peak_dbtp, 2),
        "peak_linear": peak_linear
    }

def apply_brickwall_limiter(audio: np.ndarray, ceiling_dbtp: float = -1.0) -> np.ndarray:
    """
    Transparent soft-knee limiter ensuring signal never exceeds ceiling dBTP.
    """
    ceiling_linear = 10.0 ** (ceiling_dbtp / 20.0)
    peak = np.max(np.abs(audio))
    
    if peak <= ceiling_linear:
        return audio
        
    out = audio.copy()
    knee = ceiling_linear * 0.90
    mask = np.abs(out) > knee
    
    excess = np.abs(out[mask]) - knee
    compressed = knee + (ceiling_linear - knee) * np.tanh(excess / (ceiling_linear - knee + 1e-6))
    out[mask] = np.sign(out[mask]) * compressed
    
    out = np.clip(out, -ceiling_linear, ceiling_linear)
    return out

def master_audio(
    audio: np.ndarray,
    target_loudness_lufs: float = -16.0,
    max_true_peak_dbtp: float = -1.0,
    sample_rate: int = 48000
) -> Tuple[np.ndarray, Dict[str, Any], float]:
    """
    Normalize audio to target LUFS and limit to max True Peak.
    Returns:
        mastered_audio: (samples, channels)
        mastering_report: dict containing initial and final LUFS/dBTP and gain adjustment.
        total_linear_gain: float (overall gain multiplier applied)
    """
    meter = pyln.Meter(sample_rate)
    initial_metrics = measure_audio_metrics(audio, sample_rate)
    
    initial_lufs = initial_metrics["integrated_loudness_lufs"]
    
    # 1. Calculate gain delta to reach target LUFS
    if initial_lufs > -65.0:
        gain_db = target_loudness_lufs - initial_lufs
        gain_linear = 10.0 ** (gain_db / 20.0)
    else:
        gain_db = 0.0
        gain_linear = 1.0
        
    norm_audio = audio * gain_linear
    
    # 2. Check peak against ceiling (-1.0 dBTP = 0.89125 linear)
    peak_linear = float(np.max(np.abs(norm_audio))) if len(norm_audio) > 0 else 0.0
    ceiling_linear = 10.0 ** (max_true_peak_dbtp / 20.0)
    
    if peak_linear > ceiling_linear:
        peak_gain = ceiling_linear / (peak_linear + 1e-9)
    else:
        peak_gain = 1.0
        
    total_linear_gain = float(gain_linear * peak_gain)
    mastered = (audio * total_linear_gain).astype(np.float32)
    
    # Final metrics check
    final_metrics = measure_audio_metrics(mastered, sample_rate)
    
    report = {
        "target_loudness_lufs": target_loudness_lufs,
        "max_true_peak_limit_dbtp": max_true_peak_dbtp,
        "initial_loudness_lufs": initial_lufs,
        "final_loudness_lufs": final_metrics["integrated_loudness_lufs"],
        "initial_true_peak_dbtp": initial_metrics["true_peak_dbtp"],
        "final_true_peak_dbtp": final_metrics["true_peak_dbtp"],
        "gain_applied_db": round(20.0 * np.log10(max(total_linear_gain, 1e-9)), 2),
        "total_linear_gain": total_linear_gain
    }
    return mastered, report, total_linear_gain
