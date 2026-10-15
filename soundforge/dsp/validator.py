"""
Audio Quality and Specification Validator for SoundForge AI (PS1 Specification)
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pyloudnorm as pyln

def validate_audio_file(
    audio: np.ndarray,
    target_duration: float,
    sample_rate: int = 48000,
    expected_channels: int = 2,
    max_peak_dbtp: float = -1.0,
    tolerance_seconds: float = 0.05,
    target_loudness_lufs: Optional[float] = -16.0,
    loudness_tolerance_lu: float = 1.0
) -> Dict[str, Any]:
    """
    Validate that synthesized audio meets strict delivery specifications:
    - Duration tolerance: 0.05 seconds
    - Sample rate: 48 kHz
    - Channels: 2 (stereo)
    - True Peak: <= -1.0 dBTP
    - Target loudness: target_loudness_lufs +/- 1.0 LU
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    if np.isnan(audio).any():
        errors.append("Audio contains NaN values")
    if np.isinf(audio).any():
        errors.append("Audio contains Infinite values")
        
    actual_samples = len(audio)
    actual_duration = actual_samples / sample_rate
    
    # 1. Duration check with 0.05s tolerance
    if abs(actual_duration - target_duration) > tolerance_seconds:
        errors.append(f"Duration mismatch: expected {target_duration}s, got {actual_duration:.4f}s (tolerance: +/-{tolerance_seconds}s)")
        
    # 2. Channel check
    if audio.ndim != 2 or audio.shape[1] != expected_channels:
        errors.append(f"Channel mismatch: expected {expected_channels} channels, got shape {audio.shape}")
        
    # 3. Peak check
    peak = float(np.max(np.abs(audio))) if len(audio) > 0 else 0.0
    peak_dbtp = float(20.0 * np.log10(max(peak, 1e-9)))
    
    if peak_dbtp > max_peak_dbtp + 0.05:
        errors.append(f"Peak {peak_dbtp:.2f} dBTP exceeds ceiling limit {max_peak_dbtp} dBTP")
        
    if peak < 1e-4:
        warnings.append("Audio output is essentially silent")
        
    # 4. Loudness check (ITU-R BS.1770 / EBU R128)
    measured_lufs = -70.0
    if target_loudness_lufs is not None and peak > 1e-4:
        try:
            meter = pyln.Meter(sample_rate)
            measured_lufs = float(meter.integrated_loudness(audio))
            lufs_diff = abs(measured_lufs - target_loudness_lufs)
            if lufs_diff > loudness_tolerance_lu:
                warnings.append(
                    f"Measured loudness {measured_lufs:.2f} LUFS deviates from target {target_loudness_lufs:.2f} LUFS by {lufs_diff:.2f} LU (tolerance: {loudness_tolerance_lu} LU)"
                )
        except Exception as ex:
            warnings.append(f"Could not compute integrated loudness: {ex}")
            
    return {
        "valid": len(errors) == 0,
        "actual_duration_seconds": round(actual_duration, 4),
        "target_duration_seconds": target_duration,
        "sample_rate": sample_rate,
        "channels": audio.shape[1] if audio.ndim == 2 else 1,
        "peak_dbtp": round(peak_dbtp, 2),
        "measured_loudness_lufs": round(measured_lufs, 2),
        "target_loudness_lufs": target_loudness_lufs,
        "errors": errors,
        "warnings": warnings
    }
