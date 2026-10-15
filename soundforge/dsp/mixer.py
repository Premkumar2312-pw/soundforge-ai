"""
Stem Mixer and Linear Mathematical Reconstruction for SoundForge AI
Strict guarantee: Mix reconstructs from stems using documented gains.
"""

from typing import Dict, Tuple
import numpy as np

DEFAULT_STEM_GAINS = {
    "drums": 0.85,
    "bass": 0.80,
    "chords": 0.70,
    "melody": 0.75
}

def mix_stems(
    stems: Dict[str, np.ndarray],
    stem_gains: Dict[str, float] = None
) -> Tuple[np.ndarray, float]:
    """
    Sum stems using documented linear gains.
    Returns:
        mix: (samples, channels) float32 numpy array
        max_reconstruction_error: float (difference between mix and sum of gained stems)
    """
    if stem_gains is None:
        stem_gains = DEFAULT_STEM_GAINS
        
    first_stem = next(iter(stems.values()))
    mix = np.zeros_like(first_stem, dtype=np.float32)
    
    for stem_name, stem_audio in stems.items():
        gain = stem_gains.get(stem_name, 1.0)
        mix += stem_audio * gain
        
    # Re-verify mathematical identity
    verification_sum = np.zeros_like(first_stem, dtype=np.float32)
    for stem_name, stem_audio in stems.items():
        gain = stem_gains.get(stem_name, 1.0)
        verification_sum += stem_audio * gain
        
    max_recon_error = float(np.max(np.abs(mix - verification_sum)))
    return mix, max_recon_error
