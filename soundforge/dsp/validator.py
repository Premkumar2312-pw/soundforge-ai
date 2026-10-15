"""
Audio Quality and Specification Validator for SoundForge AI
"""

from typing import Dict, Any, List
import numpy as np

def validate_audio_file(
    audio: np.ndarray,
    target_duration: float,
    sample_rate: int = 48000,
    expected_channels: int = 2,
    max_peak_dbtp: float = -1.0,
    tolerance_seconds: float = 0.005
) -> Dict[str, Any]:
    """
    Validate that synthesized audio meets strict delivery specifications.
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    if np.isnan(audio).any():
        errors.append("Audio contains NaN values")
    if np.isinf(audio).any():
        errors.append("Audio contains Infinite values")
        
    actual_samples = len(audio)
    actual_duration = actual_samples / sample_rate
    
    if abs(actual_duration - target_duration) > tolerance_seconds:
        errors.append(f"Duration mismatch: expected {target_duration}s, got {actual_duration:.4f}s")
        
    if audio.ndim != 2 or audio.shape[1] != expected_channels:
        errors.append(f"Channel mismatch: expected {expected_channels} channels, got shape {audio.shape}")
        
    peak = float(np.max(np.abs(audio))) if len(audio) > 0 else 0.0
    peak_dbtp = float(20.0 * np.log10(max(peak, 1e-9)))
    
    if peak_dbtp > max_peak_dbtp + 0.1:  # Allow 0.1 dB margin for intersample peaks
        warnings.append(f"Peak {peak_dbtp:.2f} dBTP exceeds target {max_peak_dbtp} dBTP")
        
    if peak < 1e-4:
        warnings.append("Audio output is essentially silent")
        
    return {
        "valid": len(errors) == 0,
        "actual_duration_seconds": round(actual_duration, 4),
        "target_duration_seconds": target_duration,
        "sample_rate": sample_rate,
        "channels": audio.shape[1] if audio.ndim == 2 else 1,
        "peak_dbtp": round(peak_dbtp, 2),
        "errors": errors,
        "warnings": warnings
    }
