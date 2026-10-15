"""
Sidechain Narration Ducking Compressor for SoundForge AI
Ducks background music when voice/narration activity is detected.
"""

import os
import io
import math
from typing import Tuple, Dict, Any, Optional
import numpy as np
import scipy.signal as signal
import soundfile as sf
import httpx

async def load_narration_audio(narration_source: str, target_sr: int = 48000) -> np.ndarray:
    """
    Load narration from URL or local file path, returning stereo float32 audio at target_sr.
    """
    if narration_source.startswith("http://") or narration_source.startswith("https://"):
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(narration_source)
            resp.raise_for_status()
            audio_bytes = io.BytesIO(resp.content)
            data, sr = sf.read(audio_bytes, dtype='float32')
    else:
        if not os.path.exists(narration_source):
            raise FileNotFoundError(f"Narration file not found: {narration_source}")
        data, sr = sf.read(narration_source, dtype='float32')
        
    # Convert mono to stereo if needed
    if data.ndim == 1:
        data = np.column_stack((data, data))
    elif data.shape[1] > 2:
        data = data[:, :2]
        
    # Resample if sample rate doesn't match
    if sr != target_sr:
        num_samples = int(len(data) * target_sr / sr)
        resampled_left = signal.resample(data[:, 0], num_samples)
        resampled_right = signal.resample(data[:, 1], num_samples)
        data = np.column_stack((resampled_left, resampled_right)).astype(np.float32)
        
    return data

def apply_sidechain_ducking(
    instrumental: np.ndarray,
    narration: np.ndarray,
    sample_rate: int = 48000,
    ducking_attenuation_db: float = -12.0,
    attack_ms: float = 25.0,
    release_ms: float = 300.0,
    threshold_db: float = -38.0
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply smooth sidechain ducking to instrumental audio based on narration voice envelope.
    """
    total_len = len(instrumental)
    
    # Align narration length to instrumental length (pad or truncate)
    if len(narration) < total_len:
        pad_len = total_len - len(narration)
        narration_aligned = np.pad(narration, ((0, pad_len), (0, 0)))
    else:
        narration_aligned = narration[:total_len]
        
    # Mono narration signal for envelope detection
    mono_speech = np.mean(narration_aligned, axis=1)
    
    # Envelope follower using leaky integrator (fast attack, smooth release)
    attack_coeff = math.exp(-1.0 / (max(0.001, attack_ms * 0.001 * sample_rate)))
    release_coeff = math.exp(-1.0 / (max(0.001, release_ms * 0.001 * sample_rate)))
    
    rectified = np.abs(mono_speech)
    envelope = np.zeros(total_len, dtype=np.float32)
    
    env_val = 0.0
    for i in range(total_len):
        x = rectified[i]
        if x > env_val:
            env_val = attack_coeff * env_val + (1.0 - attack_coeff) * x
        else:
            env_val = release_coeff * env_val + (1.0 - release_coeff) * x
        envelope[i] = env_val
        
    # Convert envelope to dBFS
    threshold_linear = 10.0 ** (threshold_db / 20.0)
    ducking_linear = 10.0 ** (ducking_attenuation_db / 20.0)
    
    # Gain reduction curve: 1.0 when silent, ducking_linear when speaking
    gain_curve = np.ones(total_len, dtype=np.float32)
    active_mask = envelope > threshold_linear
    
    # Smooth ratio mapping
    ratio = np.clip((envelope - threshold_linear) / (0.15 - threshold_linear + 1e-6), 0.0, 1.0)
    gain_curve = 1.0 - ratio * (1.0 - ducking_linear)
    
    # Apply low-pass smoothing to the gain curve to avoid any clicking
    smooth_sos = signal.butter(2, 20.0, btype='lowpass', fs=sample_rate, output='sos')
    smoothed_gain = signal.sosfilt(smooth_sos, gain_curve)
    smoothed_gain = np.clip(smoothed_gain, ducking_linear, 1.0)
    
    ducked_instrumental = instrumental * np.column_stack((smoothed_gain, smoothed_gain))
    
    speech_active_samples = np.sum(active_mask)
    speech_active_seconds = float(speech_active_samples / sample_rate)
    
    metrics = {
        "ducking_applied": True,
        "ducking_attenuation_db": ducking_attenuation_db,
        "attack_ms": attack_ms,
        "release_ms": release_ms,
        "threshold_db": threshold_db,
        "speech_activity_seconds": round(speech_active_seconds, 2),
        "speech_percentage": round(100.0 * speech_active_seconds / (total_len / sample_rate), 1)
    }
    return ducked_instrumental.astype(np.float32), metrics
