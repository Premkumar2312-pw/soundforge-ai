"""
Procedural Multi-Stem Audio Synthesizer Engine for SoundForge AI
Strict Zero-Frequency-Splitting policy: generates 4 genuine independent stems.
Commercially cleared DSP algorithms: pure mathematics, zero proprietary samples.
"""

import math
import numpy as np
import scipy.signal as signal
from typing import Dict, List, Any, Tuple
from soundforge.models import MusicalSection

def midi_to_hz(midi_note: float) -> float:
    """Convert MIDI note number to frequency in Hertz."""
    return 440.0 * (2.0 ** ((midi_note - 69.0) / 12.0))

def generate_adsr(
    total_samples: int,
    attack_s: float,
    decay_s: float,
    sustain_level: float,
    release_s: float,
    sr: int = 48000
) -> np.ndarray:
    """Generate an ADSR envelope of exact sample length."""
    a_samples = int(attack_s * sr)
    d_samples = int(decay_s * sr)
    r_samples = int(release_s * sr)
    
    if a_samples + d_samples + r_samples >= total_samples:
        scale = total_samples / max(1, (a_samples + d_samples + r_samples))
        a_samples = int(a_samples * scale)
        d_samples = int(d_samples * scale)
        r_samples = int(r_samples * scale)
    
    s_samples = max(0, total_samples - (a_samples + d_samples + r_samples))
    
    env = []
    if a_samples > 0:
        env.append(np.linspace(0.0, 1.0, a_samples, endpoint=False))
    if d_samples > 0:
        env.append(np.linspace(1.0, sustain_level, d_samples, endpoint=False))
    if s_samples > 0:
        env.append(np.full(s_samples, sustain_level))
    if r_samples > 0:
        env.append(np.linspace(sustain_level, 0.0, r_samples))
        
    full_env = np.concatenate(env) if env else np.zeros(total_samples)
    if len(full_env) < total_samples:
        full_env = np.pad(full_env, (0, total_samples - len(full_env)))
    elif len(full_env) > total_samples:
        full_env = full_env[:total_samples]
    return full_env

class ProceduralSynthesizer:
    """Multi-stem synthesizer generating Drums, Bass, Chords, and Melody."""
    
    def __init__(self, sample_rate: int = 48000, seed: int = 42):
        self.sample_rate = sample_rate
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def synthesize_kick(self, duration_s: float = 0.45) -> np.ndarray:
        sr = self.sample_rate
        n = int(duration_s * sr)
        t = np.linspace(0, duration_s, n, endpoint=False)
        pitch = 48.0 + (170.0 - 48.0) * np.exp(-t * 30.0)
        phase = 2.0 * np.pi * np.cumsum(pitch) / sr
        sub = np.sin(phase)
        click = self.rng.uniform(-1, 1, n) * np.exp(-t * 140.0)
        amp_env = np.exp(-t * 8.0)
        body = (sub * 0.88 + click * 0.22) * amp_env
        return np.column_stack((body, body))

    def synthesize_snare(self, duration_s: float = 0.35) -> np.ndarray:
        sr = self.sample_rate
        n = int(duration_s * sr)
        t = np.linspace(0, duration_s, n, endpoint=False)
        pitch = 150.0 + (240.0 - 150.0) * np.exp(-t * 45.0)
        tone = np.sin(2.0 * np.pi * np.cumsum(pitch) / sr) * np.exp(-t * 24.0)
        noise = self.rng.uniform(-1, 1, n)
        sos = signal.butter(4, [900, 7500], btype='bandpass', fs=sr, output='sos')
        filtered_noise = signal.sosfilt(sos, noise) * np.exp(-t * 15.0)
        sound = tone * 0.45 + filtered_noise * 0.65
        return np.column_stack((sound * 0.95, sound * 1.05))

    def synthesize_hihat(self, duration_s: float = 0.08, open_hat: bool = False) -> np.ndarray:
        sr = self.sample_rate
        dur = 0.35 if open_hat else duration_s
        n = int(dur * sr)
        t = np.linspace(0, dur, n, endpoint=False)
        decay = 16.0 if open_hat else 65.0
        noise = self.rng.uniform(-1, 1, n)
        sos = signal.butter(3, 7500, btype='highpass', fs=sr, output='sos')
        filtered = signal.sosfilt(sos, noise) * np.exp(-t * decay)
        return np.column_stack((filtered * 0.8, filtered * 1.15))

    def synthesize_crash(self, duration_s: float = 1.8) -> np.ndarray:
        sr = self.sample_rate
        n = int(duration_s * sr)
        t = np.linspace(0, duration_s, n, endpoint=False)
        noise = self.rng.uniform(-1, 1, n)
        sos = signal.butter(2, [3500, 16000], btype='bandpass', fs=sr, output='sos')
        filtered = signal.sosfilt(sos, noise) * np.exp(-t * 3.5)
        return np.column_stack((filtered * 0.9, filtered * 1.1))

    def synthesize_synth_note(
        self,
        midi_note: float,
        duration_s: float,
        waveform: str = 'saw',
        cutoff_hz: float = 1600.0,
        resonance: float = 1.2,
        attack_s: float = 0.02,
        decay_s: float = 0.1,
        sustain_level: float = 0.7,
        release_s: float = 0.05,
        pan: float = 0.0,
        detune_cents: float = 0.0
    ) -> np.ndarray:
        sr = self.sample_rate
        n = int(duration_s * sr)
        if n <= 0:
            return np.zeros((0, 2), dtype=np.float32)
        t = np.linspace(0, duration_s, n, endpoint=False)
        
        freq = midi_to_hz(midi_note) * (2.0 ** (detune_cents / 1200.0))
        
        if waveform == 'saw':
            wave = signal.sawtooth(2.0 * np.pi * freq * t)
        elif waveform == 'square':
            wave = signal.square(2.0 * np.pi * freq * t)
        elif waveform == 'triangle':
            wave = signal.sawtooth(2.0 * np.pi * freq * t, width=0.5)
        else:
            wave = np.sin(2.0 * np.pi * freq * t)
            
        # Resonant filter
        nyquist = sr / 2.0
        safe_cutoff = min(max(50.0, cutoff_hz), nyquist * 0.9)
        sos = signal.butter(2, safe_cutoff, btype='lowpass', fs=sr, output='sos')
        filtered = signal.sosfilt(sos, wave)
        
        # Soft saturation
        filtered = np.tanh(filtered * 1.2)
        
        # Envelope
        env = generate_adsr(n, attack_s, decay_s, sustain_level, release_s, sr)
        audio = filtered * env
        
        # Stereo panning
        left_gain = math.cos((pan + 1.0) * math.pi / 4.0)
        right_gain = math.sin((pan + 1.0) * math.pi / 4.0)
        return np.column_stack((audio * left_gain, audio * right_gain)).astype(np.float32)

    def render_all_stems(
        self,
        duration: float,
        bpm: float,
        sections: List[MusicalSection],
        chord_progression: List[Dict[str, Any]],
        genre: str = "electronic",
        loopability: bool = False
    ) -> Dict[str, np.ndarray]:
        """
        Synthesize Drums, Bass, Chords, and Melody stems independently.
        Returns dictionary of numpy arrays (samples, 2).
        """
        sr = self.sample_rate
        total_samples = int(duration * sr)
        spb = 60.0 / bpm
        seconds_per_bar = spb * 4.0
        
        stem_drums = np.zeros((total_samples, 2), dtype=np.float32)
        stem_bass = np.zeros((total_samples, 2), dtype=np.float32)
        stem_chords = np.zeros((total_samples, 2), dtype=np.float32)
        stem_melody = np.zeros((total_samples, 2), dtype=np.float32)
        
        kick_sample = self.synthesize_kick()
        snare_sample = self.synthesize_snare()
        hihat_closed = self.synthesize_hihat(open_hat=False)
        hihat_open = self.synthesize_hihat(open_hat=True)
        crash_sample = self.synthesize_crash()
        
        num_bars = int(math.ceil(duration / seconds_per_bar))
        
        # Render section by section
        for sec in sections:
            sec_start = sec.start_time
            sec_end = min(sec.end_time, duration)
            sec_dur = sec_end - sec_start
            sec_name = sec.name.lower()
            
            # Crash cymbal on new major sections (intro, chorus)
            if ("chorus" in sec_name or "drop" in sec_name or sec_start == 0.0) and not loopability:
                idx = int(sec_start * sr)
                end_idx = min(idx + len(crash_sample), total_samples)
                stem_drums[idx:end_idx] += crash_sample[:end_idx - idx] * 0.45
            
            # Determine section intensity
            is_intro = "intro" in sec_name
            is_outro = "outro" in sec_name
            is_chorus = "chorus" in sec_name or "drop" in sec_name or "main" in sec_name
            
            bar_start_idx = int(sec_start / seconds_per_bar)
            bar_end_idx = int(math.ceil(sec_end / seconds_per_bar))
            
            for bar_i in range(bar_start_idx, bar_end_idx):
                bar_t = bar_i * seconds_per_bar
                if bar_t >= sec_end - 0.05:
                    break
                    
                chord_info = chord_progression[bar_i % len(chord_progression)]
                
                # --- 1. DRUMS RENDERING ---
                for beat in range(4):
                    beat_t = bar_t + beat * spb
                    if beat_t >= sec_end or beat_t >= duration - 0.05:
                        break
                    
                    # Kick: in verse/chorus on beats 0 & 2; four-on-floor in dance
                    kick_hits = [0, 1, 2, 3] if (genre == "dance" and is_chorus) else [0, 2]
                    if beat in kick_hits and (not is_intro or beat == 0):
                        idx = int(beat_t * sr)
                        end_idx = min(idx + len(kick_sample), total_samples)
                        stem_drums[idx:end_idx] += kick_sample[:end_idx - idx] * 0.90
                    
                    # Snare: on beats 1 & 3
                    if beat in [1, 3] and not is_intro:
                        idx = int(beat_t * sr)
                        end_idx = min(idx + len(snare_sample), total_samples)
                        stem_drums[idx:end_idx] += snare_sample[:end_idx - idx] * 0.85
                        
                    # Hi-hats: 8th notes
                    for sub in [0.0, 0.5]:
                        sub_t = beat_t + sub * spb
                        if sub_t < sec_end and sub_t < duration - 0.04:
                            idx = int(sub_t * sr)
                            hat = hihat_open if (beat == 3 and sub == 0.5) else hihat_closed
                            end_idx = min(idx + len(hat), total_samples)
                            hat_vol = 0.50 if is_chorus else 0.35
                            stem_drums[idx:end_idx] += hat[:end_idx - idx] * hat_vol

                # --- 2. CHORDS RENDERING ---
                bar_dur = min(seconds_per_bar, sec_end - bar_t)
                if bar_dur > 0.1:
                    for note in chord_info["notes"]:
                        # Stereo chorus with slight detune
                        c_audio = self.synthesize_synth_note(
                            midi_note=note,
                            duration_s=bar_dur,
                            waveform='saw' if is_chorus else 'triangle',
                            cutoff_hz=2200.0 if is_chorus else 1200.0,
                            attack_s=0.08,
                            decay_s=0.2,
                            sustain_level=0.8,
                            release_s=0.1,
                            pan=self.rng.uniform(-0.35, 0.35),
                            detune_cents=self.rng.uniform(-4.0, 4.0)
                        )
                        idx = int(bar_t * sr)
                        end_idx = min(idx + len(c_audio), total_samples)
                        stem_chords[idx:end_idx] += c_audio[:end_idx - idx] * 0.20

                # --- 3. BASS RENDERING ---
                # Groove: syncopated 8th-note root bass
                bass_hits = [0.0, 1.5, 2.0, 3.0] if not is_intro else [0.0, 2.0]
                for hit_b in bass_hits:
                    hit_t = bar_t + hit_b * spb
                    if hit_t < sec_end and hit_t < duration - 0.1:
                        bass_dur = 0.42 * spb
                        b_audio = self.synthesize_synth_note(
                            midi_note=chord_info["root"],
                            duration_s=bass_dur,
                            waveform='triangle' if is_intro else 'saw',
                            cutoff_hz=450.0 if is_intro else 750.0,
                            attack_s=0.015,
                            decay_s=0.1,
                            sustain_level=0.6,
                            release_s=0.08,
                            pan=0.0
                        )
                        idx = int(hit_t * sr)
                        end_idx = min(idx + len(b_audio), total_samples)
                        stem_bass[idx:end_idx] += b_audio[:end_idx - idx] * 0.85

                # --- 4. MELODY RENDERING ---
                # Melodic motif generator
                if not is_intro:
                    # Lead notes selected from chord tones and pentatonic scale
                    lead_notes = chord_info["notes"]
                    motif_steps = [
                        (0.0, 0.5, lead_notes[0] + 12),
                        (0.5, 0.5, lead_notes[1] + 12),
                        (1.0, 1.0, lead_notes[2] + 12),
                        (2.0, 0.5, lead_notes[1] + 12),
                        (2.5, 0.5, lead_notes[0] + 12),
                        (3.0, 1.0, lead_notes[3] + 12) if len(lead_notes) > 3 else (3.0, 1.0, lead_notes[0] + 12)
                    ]
                    for rel_beat, note_dur_beats, midi_n in motif_steps:
                        m_t = bar_t + rel_beat * spb
                        if m_t < sec_end and m_t < duration - 0.1:
                            m_dur = note_dur_beats * spb * 0.88
                            m_audio = self.synthesize_synth_note(
                                midi_note=midi_n,
                                duration_s=m_dur,
                                waveform='square' if is_chorus else 'triangle',
                                cutoff_hz=2800.0 if is_chorus else 1800.0,
                                attack_s=0.02,
                                decay_s=0.12,
                                sustain_level=0.7,
                                release_s=0.08,
                                pan=0.25
                            )
                            idx = int(m_t * sr)
                            end_idx = min(idx + len(m_audio), total_samples)
                            stem_melody[idx:end_idx] += m_audio[:end_idx - idx] * 0.40

        # Boundary ending conditioning
        if loopability:
            # Seamless loop: ensure first 20ms and last 20ms have equal phase/smooth micro-taper
            taper_len = int(0.02 * sr)
            taper_in = np.linspace(0.0, 1.0, taper_len)
            taper_out = np.linspace(1.0, 0.0, taper_len)
            for stem in [stem_drums, stem_bass, stem_chords, stem_melody]:
                stem[:taper_len, 0] *= taper_in
                stem[:taper_len, 1] *= taper_in
                stem[-taper_len:, 0] *= taper_out
                stem[-taper_len:, 1] *= taper_out
        else:
            # Purposeful ending: cadence hold + smooth natural fade-out tail over last 0.35s
            fade_len = int(min(0.35 * sr, total_samples * 0.15))
            if fade_len > 0:
                fade_curve = np.linspace(1.0, 0.0, fade_len) ** 1.5
                for stem in [stem_drums, stem_bass, stem_chords, stem_melody]:
                    stem[-fade_len:, 0] *= fade_curve
                    stem[-fade_len:, 1] *= fade_curve
                    
        return {
            "drums": stem_drums,
            "bass": stem_bass,
            "chords": stem_chords,
            "melody": stem_melody
        }
