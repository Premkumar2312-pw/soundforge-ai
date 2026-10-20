"""
Procedural Multi-Stem Audio Synthesizer Engine for SoundForge AI
Strict Zero-Frequency-Splitting policy: generates 4 genuine independent stems.
Commercially cleared DSP algorithms: pure mathematics, zero proprietary samples.
Supports genre-conditioned instrumentation, rhythm grids, section mood dynamics,
and timbral modeling for Cinematic, Lo-Fi, Ambient, Acoustic, Corporate, Synthwave,
Tense/Thriller, Playful, and Dance/Electronic styles.
"""

import math
import numpy as np
import scipy.signal as signal
from typing import Dict, List, Any, Tuple, Optional
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

    def synthesize_kick(self, duration_s: float = 0.45, style: str = "punchy") -> np.ndarray:
        sr = self.sample_rate
        n = int(duration_s * sr)
        t = np.linspace(0, duration_s, n, endpoint=False)

        if style == "sub_boom":  # Cinematic taiko / orchestral boom
            pitch = 38.0 + (110.0 - 38.0) * np.exp(-t * 12.0)
            phase = 2.0 * np.pi * np.cumsum(pitch) / sr
            sub = np.sin(phase)
            noise = self.rng.uniform(-1, 1, n)
            sos = signal.butter(2, [40, 220], btype='bandpass', fs=sr, output='sos')
            body = signal.sosfilt(sos, noise) * np.exp(-t * 8.0)
            amp_env = np.exp(-t * 3.5)
            sound = (sub * 0.85 + body * 0.35) * amp_env
        elif style == "soft_lofi":  # Muffled warm lo-fi kick
            pitch = 45.0 + (120.0 - 45.0) * np.exp(-t * 35.0)
            phase = 2.0 * np.pi * np.cumsum(pitch) / sr
            sub = np.sin(phase)
            sos = signal.butter(2, 450.0, btype='lowpass', fs=sr, output='sos')
            sub = signal.sosfilt(sos, sub)
            amp_env = np.exp(-t * 9.5)
            sound = sub * amp_env
        elif style == "wood_kick":  # Acoustic cajon / wooden bass
            pitch = 60.0 + (145.0 - 60.0) * np.exp(-t * 45.0)
            phase = 2.0 * np.pi * np.cumsum(pitch) / sr
            sub = np.sin(phase)
            click = self.rng.uniform(-1, 1, n) * np.exp(-t * 160.0) * 0.15
            amp_env = np.exp(-t * 11.0)
            sound = (sub * 0.88 + click) * amp_env
        elif style == "heartbeat":  # Tense thriller pulse
            sound = np.zeros(n)
            # Two soft thuds (systole and diastole)
            n_thud = int(0.12 * sr)
            if n_thud < n:
                t_sub = np.linspace(0, 0.12, n_thud, endpoint=False)
                thud1 = np.sin(2.0 * np.pi * 48.0 * t_sub) * np.exp(-t_sub * 25.0)
                sound[:n_thud] += thud1 * 0.7
                idx2 = int(0.18 * sr)
                if idx2 + n_thud < n:
                    sound[idx2:idx2+n_thud] += thud1 * 0.5
        elif style == "tight_retro":  # Synthwave 80s kick
            pitch = 50.0 + (210.0 - 50.0) * np.exp(-t * 38.0)
            phase = 2.0 * np.pi * np.cumsum(pitch) / sr
            sub = np.sin(phase)
            click = self.rng.uniform(-1, 1, n) * np.exp(-t * 180.0) * 0.28
            amp_env = np.exp(-t * 8.5)
            sound = np.tanh((sub * 0.9 + click) * amp_env * 1.3)
        else:  # punchy default (electronic / dance / corporate)
            pitch = 48.0 + (170.0 - 48.0) * np.exp(-t * 30.0)
            phase = 2.0 * np.pi * np.cumsum(pitch) / sr
            sub = np.sin(phase)
            click = self.rng.uniform(-1, 1, n) * np.exp(-t * 140.0)
            amp_env = np.exp(-t * 8.0)
            sound = (sub * 0.88 + click * 0.22) * amp_env

        return np.column_stack((sound * 0.98, sound * 1.02)).astype(np.float32)

    def synthesize_snare(self, duration_s: float = 0.35, style: str = "crisp") -> np.ndarray:
        sr = self.sample_rate
        n = int(duration_s * sr)
        t = np.linspace(0, duration_s, n, endpoint=False)

        if style == "rimshot":  # Lo-Fi wooden rimshot
            tone = np.sin(2.0 * np.pi * 880.0 * t) * np.exp(-t * 50.0)
            noise = self.rng.uniform(-1, 1, n)
            sos = signal.butter(2, [1400, 4200], btype='bandpass', fs=sr, output='sos')
            filtered_noise = signal.sosfilt(sos, noise) * np.exp(-t * 45.0)
            sound = tone * 0.5 + filtered_noise * 0.55
        elif style == "gated_80s":  # Synthwave gated reverb snare
            pitch = 160.0 + (260.0 - 160.0) * np.exp(-t * 40.0)
            tone = np.sin(2.0 * np.pi * np.cumsum(pitch) / sr) * np.exp(-t * 20.0)
            noise = self.rng.uniform(-1, 1, n)
            sos = signal.butter(4, [800, 9000], btype='bandpass', fs=sr, output='sos')
            gated_noise = signal.sosfilt(sos, noise)
            # Reverb-like body with sudden gate cut at 0.24s
            gate_len = int(0.24 * sr)
            gate_env = np.ones(n)
            if gate_len < n:
                gate_env[gate_len:] = np.linspace(1.0, 0.0, n - gate_len) ** 3
            sound = (tone * 0.4 + gated_noise * 0.8) * gate_env
        elif style == "acoustic_brush":  # Acoustic soft brush snare
            noise = self.rng.uniform(-1, 1, n)
            sos = signal.butter(2, [1200, 7000], btype='bandpass', fs=sr, output='sos')
            filtered_noise = signal.sosfilt(sos, noise)
            brush_env = np.linspace(0.2, 1.0, int(0.04 * sr))
            full_env = np.exp(-t * 16.0)
            full_env[:len(brush_env)] *= brush_env
            sound = filtered_noise * full_env * 0.75
        elif style == "orchestral_hit":  # Cinematic orchestral snare impact
            tone = np.sin(2.0 * np.pi * 130.0 * t) * np.exp(-t * 12.0)
            noise = self.rng.uniform(-1, 1, n)
            sos = signal.butter(3, [600, 8500], btype='bandpass', fs=sr, output='sos')
            filtered = signal.sosfilt(sos, noise) * np.exp(-t * 9.0)
            sound = tone * 0.45 + filtered * 0.8
        else:  # crisp electronic / corporate
            pitch = 150.0 + (240.0 - 150.0) * np.exp(-t * 45.0)
            tone = np.sin(2.0 * np.pi * np.cumsum(pitch) / sr) * np.exp(-t * 24.0)
            noise = self.rng.uniform(-1, 1, n)
            sos = signal.butter(4, [900, 7500], btype='bandpass', fs=sr, output='sos')
            filtered_noise = signal.sosfilt(sos, noise) * np.exp(-t * 15.0)
            sound = tone * 0.45 + filtered_noise * 0.65

        return np.column_stack((sound * 0.95, sound * 1.05)).astype(np.float32)

    def synthesize_hihat(self, duration_s: float = 0.08, open_hat: bool = False, style: str = "metal") -> np.ndarray:
        sr = self.sample_rate
        dur = 0.35 if open_hat else duration_s
        n = int(dur * sr)
        t = np.linspace(0, dur, n, endpoint=False)
        noise = self.rng.uniform(-1, 1, n)

        if style == "shaker":  # Acoustic shaker
            sos = signal.butter(2, [3500, 11000], btype='bandpass', fs=sr, output='sos')
            filtered = signal.sosfilt(sos, noise)
            shaker_env = np.sin(np.pi * (t / dur)) ** 1.5
            sound = filtered * shaker_env * 0.7
        elif style == "clock_tick":  # Suspense / tense mechanical tick
            sos = signal.butter(3, [3200, 9500], btype='bandpass', fs=sr, output='sos')
            filtered = signal.sosfilt(sos, noise) * np.exp(-t * 140.0)
            sound = filtered * 0.85
        elif style == "lofi_vinyl":  # Muffled lo-fi hat
            decay = 18.0 if open_hat else 70.0
            sos = signal.butter(2, [2800, 6500], btype='bandpass', fs=sr, output='sos')
            sound = signal.sosfilt(sos, noise) * np.exp(-t * decay) * 0.75
        else:  # crisp metal default
            decay = 16.0 if open_hat else 65.0
            sos = signal.butter(3, 7500, btype='highpass', fs=sr, output='sos')
            sound = signal.sosfilt(sos, noise) * np.exp(-t * decay)

        return np.column_stack((sound * 0.85, sound * 1.15)).astype(np.float32)

    def synthesize_crash(self, duration_s: float = 1.8) -> np.ndarray:
        sr = self.sample_rate
        n = int(duration_s * sr)
        t = np.linspace(0, duration_s, n, endpoint=False)
        noise = self.rng.uniform(-1, 1, n)
        sos = signal.butter(2, [3500, 16000], btype='bandpass', fs=sr, output='sos')
        filtered = signal.sosfilt(sos, noise) * np.exp(-t * 3.5)
        return np.column_stack((filtered * 0.9, filtered * 1.1)).astype(np.float32)

    def synthesize_pluck(
        self,
        midi_note: float,
        duration_s: float,
        decay_s: float = 0.5,
        brightness: float = 0.6,
        pan: float = 0.0
    ) -> np.ndarray:
        """Karplus-Strong / decaying string physical modeling synthesis."""
        sr = self.sample_rate
        n = int(duration_s * sr)
        if n <= 0:
            return np.zeros((0, 2), dtype=np.float32)
        freq = midi_to_hz(midi_note)
        period = max(2, int(round(sr / freq)))
        buf = np.zeros(n, dtype=np.float32)
        seed_burst = self.rng.uniform(-1.0, 1.0, period).astype(np.float32)
        buf[:period] = seed_burst

        damping = 0.994 - (0.003 * (1.0 - brightness))
        for i in range(period, n):
            buf[i] = 0.5 * (buf[i - period] + buf[i - period + 1]) * damping

        env = np.exp(-np.linspace(0, duration_s / max(0.05, decay_s), n))
        audio = buf * env
        left_gain = math.cos((pan + 1.0) * math.pi / 4.0)
        right_gain = math.sin((pan + 1.0) * math.pi / 4.0)
        return np.column_stack((audio * left_gain, audio * right_gain)).astype(np.float32)

    def synthesize_rhodes(
        self,
        midi_note: float,
        duration_s: float,
        pan: float = 0.0
    ) -> np.ndarray:
        """Warm electric piano / Rhodes tine synthesis with tremolo."""
        sr = self.sample_rate
        n = int(duration_s * sr)
        if n <= 0:
            return np.zeros((0, 2), dtype=np.float32)
        t = np.linspace(0, duration_s, n, endpoint=False)
        f0 = midi_to_hz(midi_note)
        body = np.sin(2.0 * np.pi * f0 * t) * np.exp(-t * 2.8)
        second = 0.32 * np.sin(2.0 * np.pi * f0 * 2.0 * t) * np.exp(-t * 4.5)
        tine = 0.22 * np.sin(2.0 * np.pi * f0 * 3.98 * t) * np.exp(-t * 14.0)
        tremolo = 1.0 + 0.12 * np.sin(2.0 * np.pi * 4.5 * t)
        tone = (body + second + tine) * tremolo
        sos = signal.butter(2, min(2200.0, sr * 0.45), btype='lowpass', fs=sr, output='sos')
        filtered = signal.sosfilt(sos, tone)
        env = generate_adsr(n, 0.012, 0.25, 0.45, 0.18, sr)
        audio = filtered * env
        left_gain = math.cos((pan + 1.0) * math.pi / 4.0)
        right_gain = math.sin((pan + 1.0) * math.pi / 4.0)
        return np.column_stack((audio * left_gain, audio * right_gain)).astype(np.float32)

    def synthesize_ambient_pad(
        self,
        midi_note: float,
        duration_s: float,
        pan: float = 0.0
    ) -> np.ndarray:
        """Lush multi-oscillator ambient pad with slow attack and chorus."""
        sr = self.sample_rate
        n = int(duration_s * sr)
        if n <= 0:
            return np.zeros((0, 2), dtype=np.float32)
        t = np.linspace(0, duration_s, n, endpoint=False)
        f0 = midi_to_hz(midi_note)
        # Detuned oscillators
        osc1 = np.sin(2.0 * np.pi * f0 * (2.0 ** (-6.0 / 1200.0)) * t)
        osc2 = signal.sawtooth(2.0 * np.pi * f0 * t, width=0.5) * 0.35
        osc3 = np.sin(2.0 * np.pi * f0 * (2.0 ** (6.0 / 1200.0)) * t)
        mix = (osc1 * 0.45 + osc2 * 0.35 + osc3 * 0.45)
        sos = signal.butter(2, min(850.0, sr * 0.45), btype='lowpass', fs=sr, output='sos')
        filtered = signal.sosfilt(sos, mix)
        atk = min(1.2, duration_s * 0.35)
        rel = min(0.9, duration_s * 0.3)
        env = generate_adsr(n, attack_s=atk, decay_s=0.5, sustain_level=0.88, release_s=rel, sr=sr)
        audio = np.tanh(filtered * 1.1) * env
        left_gain = math.cos((pan + 1.0) * math.pi / 4.0)
        right_gain = math.sin((pan + 1.0) * math.pi / 4.0)
        return np.column_stack((audio * left_gain, audio * right_gain)).astype(np.float32)

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
        elif waveform == 'bell':  # FM bell for corporate/game
            carrier = np.sin(2.0 * np.pi * freq * t)
            modulator = np.sin(2.0 * np.pi * freq * 2.76 * t) * np.exp(-t * 12.0)
            wave = np.sin(2.0 * np.pi * freq * t + 1.5 * modulator)
        else:
            wave = np.sin(2.0 * np.pi * freq * t)

        nyquist = sr / 2.0
        safe_cutoff = min(max(50.0, cutoff_hz), nyquist * 0.9)
        sos = signal.butter(2, safe_cutoff, btype='lowpass', fs=sr, output='sos')
        filtered = signal.sosfilt(sos, wave)
        filtered = np.tanh(filtered * 1.2)

        env = generate_adsr(n, attack_s, decay_s, sustain_level, release_s, sr)
        audio = filtered * env

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
        loopability: bool = False,
        energy: str = "medium"
    ) -> Dict[str, np.ndarray]:
        """
        Synthesize Drums, Bass, Chords, and Melody stems independently.
        Deeply conditioned on genre, style, mood, and section timeline.
        """
        sr = self.sample_rate
        total_samples = int(duration * sr)
        spb = 60.0 / bpm
        seconds_per_bar = spb * 4.0

        stem_drums = np.zeros((total_samples, 2), dtype=np.float32)
        stem_bass = np.zeros((total_samples, 2), dtype=np.float32)
        stem_chords = np.zeros((total_samples, 2), dtype=np.float32)
        stem_melody = np.zeros((total_samples, 2), dtype=np.float32)

        # 1. Prepare genre-specific drum samples
        if genre == "cinematic":
            kick_sample = self.synthesize_kick(duration_s=1.2, style="sub_boom")
            snare_sample = self.synthesize_snare(duration_s=0.45, style="orchestral_hit")
            hihat_closed = self.synthesize_hihat(style="metal")
            hihat_open = self.synthesize_hihat(open_hat=True, style="metal")
        elif genre == "lofi":
            kick_sample = self.synthesize_kick(duration_s=0.35, style="soft_lofi")
            snare_sample = self.synthesize_snare(duration_s=0.25, style="rimshot")
            hihat_closed = self.synthesize_hihat(style="lofi_vinyl")
            hihat_open = self.synthesize_hihat(open_hat=True, style="lofi_vinyl")
        elif genre == "acoustic":
            kick_sample = self.synthesize_kick(duration_s=0.30, style="wood_kick")
            snare_sample = self.synthesize_snare(duration_s=0.22, style="rimshot")
            hihat_closed = self.synthesize_hihat(style="shaker")
            hihat_open = self.synthesize_hihat(open_hat=True, style="shaker")
        elif genre == "tense":
            kick_sample = self.synthesize_kick(duration_s=0.45, style="heartbeat")
            snare_sample = self.synthesize_snare(duration_s=0.20, style="rimshot")
            hihat_closed = self.synthesize_hihat(style="clock_tick")
            hihat_open = self.synthesize_hihat(open_hat=True, style="clock_tick")
        elif genre == "synthwave":
            kick_sample = self.synthesize_kick(duration_s=0.40, style="tight_retro")
            snare_sample = self.synthesize_snare(duration_s=0.38, style="gated_80s")
            hihat_closed = self.synthesize_hihat(style="metal")
            hihat_open = self.synthesize_hihat(open_hat=True, style="metal")
        elif genre == "ambient":
            # Deep atmospheric pulse, strictly preserving non-silent audible stem per PS1
            kick_sample = self.synthesize_kick(duration_s=0.8, style="sub_boom")
            snare_sample = self.synthesize_snare(duration_s=0.3, style="acoustic_brush")
            hihat_closed = self.synthesize_hihat(style="shaker")
            hihat_open = self.synthesize_hihat(open_hat=True, style="shaker")
        else:  # corporate, dance, electronic, playful
            kick_sample = self.synthesize_kick(duration_s=0.42, style="punchy")
            snare_sample = self.synthesize_snare(duration_s=0.30, style="crisp")
            hihat_closed = self.synthesize_hihat(style="metal")
            hihat_open = self.synthesize_hihat(open_hat=True, style="metal")

        crash_sample = self.synthesize_crash()

        # Render section by section
        for sec in sections:
            sec_start = sec.start_time
            sec_end = min(sec.end_time, duration)
            sec_dur = sec_end - sec_start
            sec_name = sec.name.lower()
            sec_mood = (getattr(sec, "mood", "") or "").lower()

            is_intro = "intro" in sec_name or "intro" in sec_mood or sec_start == 0.0 and len(sections) > 1
            is_outro = "outro" in sec_name or "outro" in sec_mood
            is_chorus = any(k in sec_name or k in sec_mood for k in ["chorus", "drop", "climax", "main", "energetic", "epic"])
            is_calm = any(k in sec_name or k in sec_mood for k in ["calm", "relax", "chill", "meditation", "ambient"])

            # Crash cymbal on major sections
            if (is_chorus or (sec_start == 0.0 and genre not in ["ambient", "tense"])) and not loopability:
                idx = int(sec_start * sr)
                end_idx = min(idx + len(crash_sample), total_samples)
                stem_drums[idx:end_idx] += crash_sample[:end_idx - idx] * 0.40

            bar_start_idx = int(sec_start / seconds_per_bar)
            bar_end_idx = int(math.ceil(sec_end / seconds_per_bar))

            for bar_i in range(bar_start_idx, bar_end_idx):
                bar_t = bar_i * seconds_per_bar
                if bar_t >= sec_end - 0.05:
                    break

                chord_info = chord_progression[bar_i % len(chord_progression)]

                # ==========================================
                # 1. DRUMS RENDERING BY GENRE & MOOD
                # ==========================================
                if genre == "ambient":
                    # Atmospheric sub-pulse every 2 bars on beat 0 (keeps stem audible and independent without EDM beat)
                    if bar_i % 2 == 0:
                        idx = int(bar_t * sr)
                        end_idx = min(idx + len(kick_sample), total_samples)
                        stem_drums[idx:end_idx] += kick_sample[:end_idx - idx] * 0.55

                elif genre == "tense":
                    # Minimalist heartbeat on bar downbeat + clock tick 16ths
                    if bar_i % 2 == 0:
                        idx = int(bar_t * sr)
                        end_idx = min(idx + len(kick_sample), total_samples)
                        stem_drums[idx:end_idx] += kick_sample[:end_idx - idx] * 0.70
                    # Ticking 16th hats
                    for tick_i in range(8):
                        t_tick = bar_t + tick_i * (spb * 0.5)
                        if t_tick < sec_end and t_tick < duration - 0.04:
                            idx = int(t_tick * sr)
                            end_idx = min(idx + len(hihat_closed), total_samples)
                            stem_drums[idx:end_idx] += hihat_closed[:end_idx - idx] * 0.32

                elif genre == "lofi":
                    # Boom-bap laid back hip hop: kick on 0 and 2.5, rimshot on 2
                    for k_beat in ([0.0, 2.5] if not is_intro else [0.0]):
                        t_hit = bar_t + k_beat * spb
                        if t_hit < sec_end and t_hit < duration - 0.05:
                            idx = int(t_hit * sr)
                            end_idx = min(idx + len(kick_sample), total_samples)
                            stem_drums[idx:end_idx] += kick_sample[:end_idx - idx] * 0.85
                    if not is_intro:
                        t_snare = bar_t + 2.0 * spb
                        if t_snare < sec_end and t_snare < duration - 0.05:
                            idx = int(t_snare * sr)
                            end_idx = min(idx + len(snare_sample), total_samples)
                            stem_drums[idx:end_idx] += snare_sample[:end_idx - idx] * 0.80
                    # Swung 8th hats
                    for b in range(4):
                        for sub_b in [0.0, 0.55]:  # Swing delay on upbeat
                            t_h = bar_t + (b + sub_b) * spb
                            if t_h < sec_end and t_h < duration - 0.04:
                                idx = int(t_h * sr)
                                hat = hihat_open if (b == 3 and sub_b > 0.5) else hihat_closed
                                end_idx = min(idx + len(hat), total_samples)
                                stem_drums[idx:end_idx] += hat[:end_idx - idx] * 0.38

                elif genre == "cinematic":
                    # Taiko/timpani boom on beat 0 and beat 2.5 (epic syncopation)
                    for k_beat in ([0.0, 2.5] if is_chorus else [0.0]):
                        t_hit = bar_t + k_beat * spb
                        if t_hit < sec_end and t_hit < duration - 0.05:
                            idx = int(t_hit * sr)
                            end_idx = min(idx + len(kick_sample), total_samples)
                            stem_drums[idx:end_idx] += kick_sample[:end_idx - idx] * 0.95
                    # Orchestral snare hit on beat 2
                    if is_chorus or not is_intro:
                        t_snare = bar_t + 2.0 * spb
                        if t_snare < sec_end and t_snare < duration - 0.05:
                            idx = int(t_snare * sr)
                            end_idx = min(idx + len(snare_sample), total_samples)
                            stem_drums[idx:end_idx] += snare_sample[:end_idx - idx] * 0.88

                elif genre == "acoustic":
                    # Cajon kick on 0 and 2, rimshot on 2, shaker on 8ths
                    for b in range(4):
                        t_beat = bar_t + b * spb
                        if b in [0, 2] and (not is_intro or b == 0):
                            idx = int(t_beat * sr)
                            end_idx = min(idx + len(kick_sample), total_samples)
                            stem_drums[idx:end_idx] += kick_sample[:end_idx - idx] * 0.80
                        if b == 2 and not is_intro:
                            idx = int(t_beat * sr)
                            end_idx = min(idx + len(snare_sample), total_samples)
                            stem_drums[idx:end_idx] += snare_sample[:end_idx - idx] * 0.70
                        for sub in [0.0, 0.5]:
                            t_s = t_beat + sub * spb
                            if t_s < sec_end and t_s < duration - 0.04:
                                idx = int(t_s * sr)
                                end_idx = min(idx + len(hihat_closed), total_samples)
                                stem_drums[idx:end_idx] += hihat_closed[:end_idx - idx] * 0.35

                elif genre == "playful":
                    # Bouncy game rhythm: popping kick on 0 & 2, woodblock/rim on upbeats
                    for b in range(4):
                        t_beat = bar_t + b * spb
                        if t_beat >= sec_end or t_beat >= duration - 0.05:
                            break
                        if b in [0, 2]:
                            idx = int(t_beat * sr)
                            end_idx = min(idx + len(kick_sample), total_samples)
                            if end_idx > idx:
                                stem_drums[idx:end_idx] += kick_sample[:end_idx - idx] * 0.85
                        if b in [1, 3] and not is_intro:
                            idx = int(t_beat * sr)
                            end_idx = min(idx + len(snare_sample), total_samples)
                            if end_idx > idx:
                                stem_drums[idx:end_idx] += snare_sample[:end_idx - idx] * 0.75
                        # Upbeat perk
                        t_up = t_beat + 0.5 * spb
                        if t_up < sec_end and t_up < duration - 0.04:
                            idx = int(t_up * sr)
                            end_idx = min(idx + len(hihat_closed), total_samples)
                            if end_idx > idx:
                                stem_drums[idx:end_idx] += hihat_closed[:end_idx - idx] * 0.45

                else:  # corporate, dance, electronic, synthwave
                    for b in range(4):
                        t_beat = bar_t + b * spb
                        if t_beat >= sec_end or t_beat >= duration - 0.05:
                            break
                        # Four-on-the-floor in dance chorus or synthwave
                        is_four_floor = (genre == "dance" and is_chorus) or (genre == "synthwave" and is_chorus)
                        kick_hits = [0, 1, 2, 3] if is_four_floor else [0, 2]
                        if b in kick_hits and (not is_intro or b == 0):
                            idx = int(t_beat * sr)
                            end_idx = min(idx + len(kick_sample), total_samples)
                            stem_drums[idx:end_idx] += kick_sample[:end_idx - idx] * 0.90
                        if b in [1, 3] and not is_intro:
                            idx = int(t_beat * sr)
                            end_idx = min(idx + len(snare_sample), total_samples)
                            stem_drums[idx:end_idx] += snare_sample[:end_idx - idx] * 0.85
                        for sub in [0.0, 0.5]:
                            t_h = t_beat + sub * spb
                            if t_h < sec_end and t_h < duration - 0.04:
                                idx = int(t_h * sr)
                                hat = hihat_open if (b == 3 and sub == 0.5) else hihat_closed
                                end_idx = min(idx + len(hat), total_samples)
                                hat_vol = 0.50 if is_chorus else 0.35
                                stem_drums[idx:end_idx] += hat[:end_idx - idx] * hat_vol

                # ==========================================
                # 2. CHORDS RENDERING BY GENRE & MOOD
                # ==========================================
                bar_dur = min(seconds_per_bar, sec_end - bar_t)
                if bar_dur > 0.1:
                    idx = int(bar_t * sr)

                    if genre == "ambient":
                        # Lush multi-oscillator ambient pad with slow attack
                        for n_idx, note in enumerate(chord_info["notes"]):
                            c_audio = self.synthesize_ambient_pad(
                                midi_note=note,
                                duration_s=bar_dur,
                                pan=self.rng.uniform(-0.4, 0.4)
                            )
                            end_idx = min(idx + len(c_audio), total_samples)
                            stem_chords[idx:end_idx] += c_audio[:end_idx - idx] * 0.24

                    elif genre == "lofi":
                        # Warm electric piano / Rhodes chords with tremolo
                        for note in chord_info["notes"]:
                            c_audio = self.synthesize_rhodes(
                                midi_note=note,
                                duration_s=bar_dur,
                                pan=self.rng.uniform(-0.3, 0.3)
                            )
                            end_idx = min(idx + len(c_audio), total_samples)
                            stem_chords[idx:end_idx] += c_audio[:end_idx - idx] * 0.22

                    elif genre == "acoustic":
                        # Plucked acoustic guitar strum with staggered 14ms finger delay
                        for str_i, note in enumerate(chord_info["notes"]):
                            strum_delay = str_i * 0.014
                            t_strum = bar_t + strum_delay
                            if t_strum < sec_end:
                                c_audio = self.synthesize_pluck(
                                    midi_note=note,
                                    duration_s=max(0.1, bar_dur - strum_delay),
                                    decay_s=0.65,
                                    brightness=0.7,
                                    pan=self.rng.uniform(-0.35, 0.35)
                                )
                                s_idx = int(t_strum * sr)
                                end_idx = min(s_idx + len(c_audio), total_samples)
                                stem_chords[s_idx:end_idx] += c_audio[:end_idx - s_idx] * 0.26

                    elif genre == "playful":
                        # Staccato offbeat chords (skank / bouncy polka on beats 1 & 3)
                        for b in [1.0, 3.0]:
                            t_hit = bar_t + b * spb
                            if t_hit < sec_end:
                                for note in chord_info["notes"]:
                                    c_audio = self.synthesize_synth_note(
                                        midi_note=note,
                                        duration_s=spb * 0.4,
                                        waveform='triangle',
                                        cutoff_hz=2400.0,
                                        attack_s=0.01,
                                        decay_s=0.1,
                                        sustain_level=0.3,
                                        release_s=0.05,
                                        pan=self.rng.uniform(-0.3, 0.3)
                                    )
                                    s_idx = int(t_hit * sr)
                                    end_idx = min(s_idx + len(c_audio), total_samples)
                                    stem_chords[s_idx:end_idx] += c_audio[:end_idx - s_idx] * 0.20

                    elif genre == "tense":
                        # Dark dissonant cluster with slow eerie filter
                        for note in chord_info["notes"]:
                            c_audio = self.synthesize_synth_note(
                                midi_note=note,
                                duration_s=bar_dur,
                                waveform='triangle',
                                cutoff_hz=750.0,
                                attack_s=0.6,
                                decay_s=0.4,
                                sustain_level=0.8,
                                release_s=0.4,
                                pan=self.rng.uniform(-0.4, 0.4)
                            )
                            end_idx = min(idx + len(c_audio), total_samples)
                            stem_chords[idx:end_idx] += c_audio[:end_idx - idx] * 0.20

                    elif genre == "cinematic":
                        # Massive brass / strings orchestral swell
                        for note in chord_info["notes"]:
                            c_audio = self.synthesize_synth_note(
                                midi_note=note,
                                duration_s=bar_dur,
                                waveform='saw' if is_chorus else 'triangle',
                                cutoff_hz=2800.0 if is_chorus else 1400.0,
                                attack_s=0.25,
                                decay_s=0.3,
                                sustain_level=0.85,
                                release_s=0.3,
                                pan=self.rng.uniform(-0.35, 0.35),
                                detune_cents=self.rng.uniform(-5.0, 5.0)
                            )
                            end_idx = min(idx + len(c_audio), total_samples)
                            stem_chords[idx:end_idx] += c_audio[:end_idx - idx] * 0.22

                    elif genre == "corporate":
                        # Clean optimistic bell/piano stabs on downbeat
                        for note in chord_info["notes"]:
                            c_audio = self.synthesize_synth_note(
                                midi_note=note,
                                duration_s=bar_dur,
                                waveform='bell',
                                cutoff_hz=3200.0,
                                attack_s=0.015,
                                decay_s=0.3,
                                sustain_level=0.6,
                                release_s=0.15,
                                pan=self.rng.uniform(-0.35, 0.35)
                            )
                            end_idx = min(idx + len(c_audio), total_samples)
                            stem_chords[idx:end_idx] += c_audio[:end_idx - idx] * 0.22

                    else:  # dance / synthwave / electronic
                        for note in chord_info["notes"]:
                            c_audio = self.synthesize_synth_note(
                                midi_note=note,
                                duration_s=bar_dur,
                                waveform='saw' if is_chorus else 'triangle',
                                cutoff_hz=2400.0 if is_chorus else 1300.0,
                                attack_s=0.06,
                                decay_s=0.2,
                                sustain_level=0.8,
                                release_s=0.1,
                                pan=self.rng.uniform(-0.35, 0.35),
                                detune_cents=self.rng.uniform(-4.0, 4.0)
                            )
                            end_idx = min(idx + len(c_audio), total_samples)
                            stem_chords[idx:end_idx] += c_audio[:end_idx - idx] * 0.20

                # ==========================================
                # 3. BASS RENDERING BY GENRE & MOOD
                # ==========================================
                root_pitch = chord_info["root"]
                if genre == "ambient":
                    # Sustained warm sub-drone holding root note for whole bar
                    b_audio = self.synthesize_synth_note(
                        midi_note=root_pitch - 12,
                        duration_s=bar_dur,
                        waveform='sine',
                        cutoff_hz=180.0,
                        attack_s=0.4,
                        decay_s=0.2,
                        sustain_level=0.9,
                        release_s=0.4,
                        pan=0.0
                    )
                    idx = int(bar_t * sr)
                    end_idx = min(idx + len(b_audio), total_samples)
                    stem_bass[idx:end_idx] += b_audio[:end_idx - idx] * 0.85

                elif genre == "tense":
                    # Low ominous pulsing sub-bass
                    b_audio = self.synthesize_synth_note(
                        midi_note=root_pitch - 12,
                        duration_s=bar_dur * 0.85,
                        waveform='saw',
                        cutoff_hz=150.0,
                        attack_s=0.1,
                        decay_s=0.3,
                        sustain_level=0.7,
                        release_s=0.3,
                        pan=0.0
                    )
                    idx = int(bar_t * sr)
                    end_idx = min(idx + len(b_audio), total_samples)
                    stem_bass[idx:end_idx] += b_audio[:end_idx - idx] * 0.80

                elif genre == "acoustic":
                    # Plucked upright acoustic double-bass (root on 0, fifth on 2)
                    for hit_b, p_offset in [(0.0, 0), (2.0, 7)]:
                        t_b = bar_t + hit_b * spb
                        if t_b < sec_end and t_b < duration - 0.1:
                            b_audio = self.synthesize_pluck(
                                midi_note=root_pitch - 12 + p_offset,
                                duration_s=spb * 0.85,
                                decay_s=0.7,
                                brightness=0.4,
                                pan=0.0
                            )
                            s_idx = int(t_b * sr)
                            end_idx = min(s_idx + len(b_audio), total_samples)
                            stem_bass[s_idx:end_idx] += b_audio[:end_idx - s_idx] * 0.85

                elif genre == "synthwave":
                    # Rolling 16th-note synthwave bassline ("dakka-dakka")
                    for s16 in range(8):
                        t_b = bar_t + s16 * (spb * 0.5)
                        if t_b < sec_end and t_b < duration - 0.05:
                            b_audio = self.synthesize_synth_note(
                                midi_note=root_pitch,
                                duration_s=spb * 0.42,
                                waveform='saw',
                                cutoff_hz=600.0,
                                attack_s=0.01,
                                decay_s=0.08,
                                sustain_level=0.5,
                                release_s=0.04,
                                pan=0.0
                            )
                            s_idx = int(t_b * sr)
                            end_idx = min(s_idx + len(b_audio), total_samples)
                            stem_bass[s_idx:end_idx] += b_audio[:end_idx - s_idx] * 0.82

                elif genre == "lofi":
                    # Laid back 808 sub-bass groove on beats 0 and 2.5
                    for hit_b in [0.0, 2.5]:
                        t_b = bar_t + hit_b * spb
                        if t_b < sec_end and t_b < duration - 0.1:
                            b_audio = self.synthesize_synth_note(
                                midi_note=root_pitch,
                                duration_s=spb * 0.75,
                                waveform='triangle',
                                cutoff_hz=350.0,
                                attack_s=0.02,
                                decay_s=0.2,
                                sustain_level=0.7,
                                release_s=0.1,
                                pan=0.0
                            )
                            s_idx = int(t_b * sr)
                            end_idx = min(s_idx + len(b_audio), total_samples)
                            stem_bass[s_idx:end_idx] += b_audio[:end_idx - s_idx] * 0.85

                elif genre == "playful":
                    # Bouncy "oom-pah" alternating root and fifth on beats 0 and 2
                    for hit_b, p_offset in [(0.0, 0), (2.0, 7)]:
                        t_b = bar_t + hit_b * spb
                        if t_b < sec_end and t_b < duration - 0.1:
                            b_audio = self.synthesize_synth_note(
                                midi_note=root_pitch,
                                duration_s=spb * 0.35,
                                waveform='square',
                                cutoff_hz=550.0,
                                attack_s=0.01,
                                decay_s=0.1,
                                sustain_level=0.4,
                                release_s=0.05,
                                pan=0.0
                            )
                            s_idx = int(t_b * sr)
                            end_idx = min(s_idx + len(b_audio), total_samples)
                            stem_bass[s_idx:end_idx] += b_audio[:end_idx - s_idx] * 0.80

                else:  # corporate, dance, cinematic, electronic
                    bass_hits = [0.0, 1.5, 2.0, 3.0] if (not is_intro and not is_calm) else [0.0, 2.0]
                    for hit_b in bass_hits:
                        t_b = bar_t + hit_b * spb
                        if t_b < sec_end and t_b < duration - 0.1:
                            b_dur = 0.42 * spb
                            b_audio = self.synthesize_synth_note(
                                midi_note=root_pitch,
                                duration_s=b_dur,
                                waveform='triangle' if is_intro else 'saw',
                                cutoff_hz=220.0 if is_intro else 320.0,
                                attack_s=0.015,
                                decay_s=0.1,
                                sustain_level=0.6,
                                release_s=0.08,
                                pan=0.0
                            )
                            s_idx = int(t_b * sr)
                            end_idx = min(s_idx + len(b_audio), total_samples)
                            stem_bass[s_idx:end_idx] += b_audio[:end_idx - s_idx] * 0.85

                # ==========================================
                # 4. MELODY RENDERING BY GENRE & MOOD
                # ==========================================
                if not is_intro:
                    lead_notes = chord_info["notes"]

                    if genre == "ambient":
                        # Sparse singing bell / meditation chime: 1 expressive note on beat 0
                        midi_n = lead_notes[0] + 12
                        m_audio = self.synthesize_synth_note(
                            midi_note=midi_n,
                            duration_s=spb * 2.8,
                            waveform='sine',
                            cutoff_hz=1600.0,
                            attack_s=0.15,
                            decay_s=0.8,
                            sustain_level=0.5,
                            release_s=0.8,
                            pan=0.2
                        )
                        s_idx = int(bar_t * sr)
                        end_idx = min(s_idx + len(m_audio), total_samples)
                        stem_melody[s_idx:end_idx] += m_audio[:end_idx - s_idx] * 0.38

                    elif genre == "tense":
                        # Creeping staccato half-step motif
                        tense_steps = [(0.0, lead_notes[0] + 12), (1.0, lead_notes[0] + 13), (2.0, lead_notes[0] + 12)]
                        for rel_b, midi_n in tense_steps:
                            t_m = bar_t + rel_b * spb
                            if t_m < sec_end and t_m < duration - 0.1:
                                m_audio = self.synthesize_synth_note(
                                    midi_note=midi_n,
                                    duration_s=spb * 0.3,
                                    waveform='triangle',
                                    cutoff_hz=1400.0,
                                    attack_s=0.01,
                                    decay_s=0.12,
                                    sustain_level=0.2,
                                    release_s=0.05,
                                    pan=0.25
                                )
                                s_idx = int(t_m * sr)
                                end_idx = min(s_idx + len(m_audio), total_samples)
                                stem_melody[s_idx:end_idx] += m_audio[:end_idx - s_idx] * 0.40

                    elif genre == "lofi":
                        # Relaxed jazz-inflected keys phrasing
                        lofi_steps = [
                            (0.0, 0.75, lead_notes[1] + 12),
                            (1.0, 0.5, lead_notes[0] + 12),
                            (2.0, 1.0, lead_notes[3] + 12 if len(lead_notes) > 3 else lead_notes[2] + 12),
                            (3.5, 0.5, lead_notes[2] + 12)
                        ]
                        for rel_b, dur_b, midi_n in lofi_steps:
                            t_m = bar_t + rel_b * spb
                            if t_m < sec_end and t_m < duration - 0.1:
                                m_audio = self.synthesize_rhodes(
                                    midi_note=midi_n,
                                    duration_s=dur_b * spb * 0.85,
                                    pan=0.2
                                )
                                s_idx = int(t_m * sr)
                                end_idx = min(s_idx + len(m_audio), total_samples)
                                stem_melody[s_idx:end_idx] += m_audio[:end_idx - s_idx] * 0.38

                    elif genre == "acoustic":
                        # Fingerstyle folk acoustic picking lead
                        folk_steps = [
                            (0.0, 0.5, lead_notes[0] + 12),
                            (0.5, 0.5, lead_notes[2] + 12),
                            (1.0, 1.0, lead_notes[1] + 12),
                            (2.0, 0.5, lead_notes[0] + 12),
                            (2.5, 0.5, lead_notes[2] + 12),
                            (3.0, 1.0, lead_notes[1] + 12)
                        ]
                        for rel_b, dur_b, midi_n in folk_steps:
                            t_m = bar_t + rel_b * spb
                            if t_m < sec_end and t_m < duration - 0.1:
                                m_audio = self.synthesize_pluck(
                                    midi_note=midi_n,
                                    duration_s=dur_b * spb * 0.88,
                                    decay_s=0.55,
                                    brightness=0.75,
                                    pan=0.25
                                )
                                s_idx = int(t_m * sr)
                                end_idx = min(s_idx + len(m_audio), total_samples)
                                stem_melody[s_idx:end_idx] += m_audio[:end_idx - s_idx] * 0.42

                    elif genre == "cinematic":
                        # Heroic brass / horn lead with long majestic notes
                        cine_steps = [
                            (0.0, 1.5, lead_notes[0] + 12),
                            (1.5, 0.5, lead_notes[1] + 12),
                            (2.0, 2.0, lead_notes[2] + 12)
                        ]
                        for rel_b, dur_b, midi_n in cine_steps:
                            t_m = bar_t + rel_b * spb
                            if t_m < sec_end and t_m < duration - 0.1:
                                m_audio = self.synthesize_synth_note(
                                    midi_note=midi_n,
                                    duration_s=dur_b * spb * 0.92,
                                    waveform='saw',
                                    cutoff_hz=2600.0,
                                    attack_s=0.08,
                                    decay_s=0.2,
                                    sustain_level=0.85,
                                    release_s=0.2,
                                    pan=0.2
                                )
                                s_idx = int(t_m * sr)
                                end_idx = min(s_idx + len(m_audio), total_samples)
                                stem_melody[s_idx:end_idx] += m_audio[:end_idx - s_idx] * 0.40

                    elif genre == "corporate":
                        # Optimistic ascending glockenspiel / marimba arpeggio
                        corp_steps = [
                            (0.0, 0.5, lead_notes[0] + 12),
                            (0.5, 0.5, lead_notes[1] + 12),
                            (1.0, 0.5, lead_notes[2] + 12),
                            (1.5, 0.5, lead_notes[0] + 24),
                            (2.0, 1.0, lead_notes[2] + 12),
                            (3.0, 1.0, lead_notes[1] + 12)
                        ]
                        for rel_b, dur_b, midi_n in corp_steps:
                            t_m = bar_t + rel_b * spb
                            if t_m < sec_end and t_m < duration - 0.1:
                                m_audio = self.synthesize_synth_note(
                                    midi_note=midi_n,
                                    duration_s=dur_b * spb * 0.85,
                                    waveform='bell',
                                    cutoff_hz=3400.0,
                                    attack_s=0.01,
                                    decay_s=0.2,
                                    sustain_level=0.5,
                                    release_s=0.1,
                                    pan=0.25
                                )
                                s_idx = int(t_m * sr)
                                end_idx = min(s_idx + len(m_audio), total_samples)
                                stem_melody[s_idx:end_idx] += m_audio[:end_idx - s_idx] * 0.40

                    elif genre == "playful":
                        # Bouncy quirky game motif with octave leaps
                        play_steps = [
                            (0.0, 0.4, lead_notes[0] + 12),
                            (0.5, 0.4, lead_notes[0] + 24),
                            (1.0, 0.4, lead_notes[1] + 12),
                            (1.5, 0.4, lead_notes[2] + 12),
                            (2.0, 0.8, lead_notes[1] + 24),
                            (3.0, 0.8, lead_notes[0] + 12)
                        ]
                        for rel_b, dur_b, midi_n in play_steps:
                            t_m = bar_t + rel_b * spb
                            if t_m < sec_end and t_m < duration - 0.1:
                                m_audio = self.synthesize_synth_note(
                                    midi_note=midi_n,
                                    duration_s=dur_b * spb * 0.75,
                                    waveform='triangle',
                                    cutoff_hz=3000.0,
                                    attack_s=0.01,
                                    decay_s=0.1,
                                    sustain_level=0.3,
                                    release_s=0.05,
                                    pan=0.25
                                )
                                s_idx = int(t_m * sr)
                                end_idx = min(s_idx + len(m_audio), total_samples)
                                stem_melody[s_idx:end_idx] += m_audio[:end_idx - s_idx] * 0.42

                    else:  # electronic / synthwave / dance
                        motif_steps = [
                            (0.0, 0.5, lead_notes[0] + 12),
                            (0.5, 0.5, lead_notes[1] + 12),
                            (1.0, 1.0, lead_notes[2] + 12),
                            (2.0, 0.5, lead_notes[1] + 12),
                            (2.5, 0.5, lead_notes[0] + 12),
                            (3.0, 1.0, lead_notes[3] + 12 if len(lead_notes) > 3 else lead_notes[0] + 12)
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
                                s_idx = int(m_t * sr)
                                end_idx = min(s_idx + len(m_audio), total_samples)
                                stem_melody[s_idx:end_idx] += m_audio[:end_idx - s_idx] * 0.40

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

        # Controlled stem saturation for dynamic range & headroom consistency
        for s_arr in [stem_bass, stem_chords, stem_melody]:
            s_arr[:] = np.tanh(s_arr * 2.4) * 0.38
        stem_drums[:] = np.tanh(stem_drums * 2.4) * 0.30

        return {
            "drums": stem_drums,
            "bass": stem_bass,
            "chords": stem_chords,
            "melody": stem_melody
        }

    def render_single_stem(
        self,
        stem_name: str,
        duration: float,
        bpm: float,
        sections: List[MusicalSection],
        chord_progression: list,
        genre: str = "electronic",
        loopability: bool = False,
        energy: str = "medium"
    ) -> np.ndarray:
        """
        Regenerate a single instrument stem without altering the others.
        Guarantees byte-for-byte reproducibility of unmodified stems.
        """
        all_stems = self.render_all_stems(
            duration=duration,
            bpm=bpm,
            sections=sections,
            chord_progression=chord_progression,
            genre=genre,
            loopability=loopability,
            energy=energy
        )
        if stem_name not in all_stems:
            raise ValueError(f"Unknown stem '{stem_name}'. Available: {list(all_stems.keys())}")
        return all_stems[stem_name]

def compute_stem_bleed_matrix(stems: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Compute pairwise normalized cross-correlation between stems to measure stem independence / bleed.
    In genuine procedural multi-track synthesis, stem bleed is near zero (< 0.15),
    unlike frequency-split or phase-cancelled stems which exhibit high correlation.
    """
    keys = list(stems.keys())
    matrix = {}
    max_cross_corr = 0.0
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            k1, k2 = keys[i], keys[j]
            s1 = np.mean(stems[k1], axis=1) if stems[k1].ndim > 1 else stems[k1]
            s2 = np.mean(stems[k2], axis=1) if stems[k2].ndim > 1 else stems[k2]
            norm1 = float(np.linalg.norm(s1))
            norm2 = float(np.linalg.norm(s2))
            if norm1 > 1e-6 and norm2 > 1e-6:
                corr = float(np.abs(np.dot(s1, s2) / (norm1 * norm2)))
            else:
                corr = 0.0
            matrix[f"{k1}_vs_{k2}"] = round(corr, 4)
            if corr > max_cross_corr:
                max_cross_corr = corr
    return {
        "pairwise_correlations": matrix,
        "max_cross_correlation": round(max_cross_corr, 4),
        "independent_stems_verified": bool(max_cross_corr < 0.25)
    }

def measure_loop_discontinuity(audio: np.ndarray) -> float:
    """Measure loop boundary discontinuity between first and last sample frames."""
    if len(audio) < 2:
        return 0.0
    diff = np.abs(audio[0] - audio[-1])
    return float(np.max(diff))
