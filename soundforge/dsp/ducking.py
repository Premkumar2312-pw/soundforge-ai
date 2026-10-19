"""
Sidechain Narration Ducking Compressor for SoundForge AI
Ducks background music when voice/narration activity is detected.
Includes SSRF safety validation, speech activity metrics, and gain envelope extraction.
"""

import os
import io
import math
import ipaddress
import urllib.parse
from typing import Tuple, Dict, Any, Optional
import numpy as np
import scipy.signal as signal
import soundfile as sf
import httpx

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10")
]

def is_ssrf_safe_url(url: str) -> Tuple[bool, str]:
    """Validate that URL does not target localhost or private subnet ranges."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported URL scheme '{parsed.scheme}'. Only http and https are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "Invalid URL: missing hostname."

    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        # Allow only if explicitly in local testing mode via env
        if os.environ.get("ALLOW_LOCAL_SSRF_TESTING") == "1":
            return True, ""
        return False, "Access to localhost and loopback targets is blocked for security."

    try:
        ip = ipaddress.ip_address(hostname)
        for net in BLOCKED_IP_NETWORKS:
            if ip in net:
                if os.environ.get("ALLOW_LOCAL_SSRF_TESTING") == "1":
                    return True, ""
                return False, f"Access to private network address {ip} is blocked for security."
    except ValueError:
        # Not a raw IP literal; hostname resolution
        pass

    return True, ""

async def load_narration_audio(narration_source: str, target_sr: int = 48000) -> np.ndarray:
    """
    Load narration from URL or local file path, returning stereo float32 audio at target_sr.
    Enforces SSRF validation, size limits (50 MB), and timeouts.
    """
    if narration_source.startswith("http://") or narration_source.startswith("https://"):
        safe, err_msg = is_ssrf_safe_url(narration_source)
        if not safe:
            raise ValueError(f"SSRF validation blocked request: {err_msg}")

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            resp = await client.get(narration_source)
            resp.raise_for_status()

            # 50 MB limit
            if len(resp.content) > 50 * 1024 * 1024:
                raise ValueError("Narration file exceeds maximum allowed size of 50 MB.")

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
    Guarantees that narration voice is NEVER mixed into the ducked output.
    Gracefully handles speech-free or completely silent narration.
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

    active_mask = envelope > threshold_linear
    speech_active_samples = int(np.sum(active_mask))
    speech_active_seconds = float(speech_active_samples / sample_rate)

    if speech_active_samples == 0:
        # Narration is completely silent or below threshold -> zero ducking attenuation
        smoothed_gain = np.ones(total_len, dtype=np.float32)
    else:
        # Smooth ratio mapping
        ratio = np.clip((envelope - threshold_linear) / (0.15 - threshold_linear + 1e-6), 0.0, 1.0)
        gain_curve = 1.0 - ratio * (1.0 - ducking_linear)

        # Apply low-pass smoothing to the gain curve to avoid any clicking
        smooth_sos = signal.butter(2, 20.0, btype='lowpass', fs=sample_rate, output='sos')
        smoothed_gain = signal.sosfilt(smooth_sos, gain_curve)
        smoothed_gain = np.clip(smoothed_gain, ducking_linear, 1.0).astype(np.float32)

    # Pure instrumental multiplied by gain curve - VOICEOVER IS NEVER MIXED IN
    ducked_instrumental = instrumental * np.column_stack((smoothed_gain, smoothed_gain))

    # Subsampled ducking envelope curve for manifest provenance (sample at ~2 Hz, max 50 points)
    num_pts = min(50, max(10, int(total_len / sample_rate * 2)))
    sample_indices = np.linspace(0, total_len - 1, num_pts, dtype=int)
    envelope_curve = [round(float(smoothed_gain[idx]), 3) for idx in sample_indices]

    metrics = {
        "ducking_applied": True,
        "ducking_attenuation_db": ducking_attenuation_db,
        "attack_ms": attack_ms,
        "release_ms": release_ms,
        "threshold_db": threshold_db,
        "speech_activity_seconds": round(speech_active_seconds, 2),
        "speech_percentage": round(100.0 * speech_active_seconds / max(0.01, total_len / sample_rate), 1),
        "ducking_envelope_curve": envelope_curve
    }
    return ducked_instrumental.astype(np.float32), metrics
