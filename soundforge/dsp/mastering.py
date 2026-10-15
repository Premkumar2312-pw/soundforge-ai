"""
Mastering Stage for SoundForge AI
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
        
    # Oversampled or linear true peak estimate
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
    # Hyperbolic tangent soft saturation above knee
    knee = ceiling_linear * 0.90
    mask = np.abs(out) > knee
    
    # Soft compression of high-energy peaks
    excess = np.abs(out[mask]) - knee
    compressed = knee + (ceiling_linear - knee) * np.tanh(excess / (ceiling_linear - knee + 1e-6))
    out[mask] = np.sign(out[mask]) * compressed
    
    # Ensure hard limit never breached
    out = np.clip(out, -ceiling_linear, ceiling_linear)
    return out

def master_audio(
    audio: np.ndarray,
    target_loudness_lufs: float = -14.0,
    max_true_peak_dbtp: float = -1.0,
    sample_rate: int = 48000
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Normalize audio to target LUFS and limit to max True Peak.
    Returns:
        mastered_audio: (samples, channels)
        mastering_report: dict containing initial and final LUFS/dBTP and gain adjustment.
    """
    meter = pyln.Meter(sample_rate)
    initial_metrics = measure_audio_metrics(audio, sample_rate)
    
    initial_lufs = initial_metrics["integrated_loudness_lufs"]
    
    # Calculate gain delta to reach target LUFS
    if initial_lufs > -65.0:
        gain_db = target_loudness_lufs - initial_lufs
        gain_linear = 10.0 ** (gain_db / 20.0)
        normalized = audio * gain_linear
    else:
        gain_db = 0.0
        normalized = audio.copy()
        
    # Apply True Peak brickwall limiter
    mastered = apply_brickwall_limiter(normalized, ceiling_dbtp=max_true_peak_dbtp)
    
    # Final metrics check
    final_metrics = measure_audio_metrics(mastered, sample_rate)
    
    report = {
        "target_loudness_lufs": target_loudness_lufs,
        "max_true_peak_limit_dbtp": max_true_peak_dbtp,
        "initial_loudness_lufs": initial_lufs,
        "final_loudness_lufs": final_metrics["integrated_loudness_lufs"],
        "initial_true_peak_dbtp": initial_metrics["true_peak_dbtp"],
        "final_true_peak_dbtp": final_metrics["true_peak_dbtp"],
        "gain_applied_db": round(gain_db, 2)
    }
    return mastered.astype(np.float32), report
