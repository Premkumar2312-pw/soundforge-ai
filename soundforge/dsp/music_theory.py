"""
Music Theory and Arrangement Engine for SoundForge AI
Handles scale generation, chord voicings, rhythm grids, and prompt analysis.
"""

import re
import math
from typing import List, Dict, Any, Tuple, Optional
from soundforge.models import MusicalSection

ROOT_PITCHES = {
    "C": 36, "C#": 37, "DB": 37,
    "D": 38, "D#": 39, "EB": 39,
    "E": 40,
    "F": 41, "F#": 42, "GB": 42,
    "G": 43, "G#": 44, "AB": 44,
    "A": 45, "A#": 46, "BB": 46,
    "B": 47
}

SCALE_INTERVALS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "pentatonic_major": [0, 2, 4, 7, 9],
    "pentatonic_minor": [0, 3, 5, 7, 10],
}

PROGRESSIONS = {
    "major": [
        [0, 7, 9, 5],     # I - V - vi - IV
        [0, 9, 5, 7],     # I - vi - IV - V
        [2, 7, 0, 5],     # ii - V - I - IV
        [0, 5, 9, 7],     # I - IV - vi - V
    ],
    "minor": [
        [0, 8, 3, 10],    # i - VI - III - VII
        [0, 5, 7, 0],     # i - iv - v - i
        [0, 10, 8, 10],   # i - VII - VI - VII
        [0, 3, 5, 7],     # i - III - iv - v
    ]
}

def analyze_prompt_musicality(prompt: str) -> Dict[str, Any]:
    """Extract musical intent, genre, BPM, and mood from natural language prompt."""
    p = prompt.lower()
    
    # Defaults
    bpm = 118.0
    key = "C_major"
    genre = "electronic"
    energy = "medium"
    
    # Genre / Mood detection
    if any(k in p for k in ["lo-fi", "lofi", "chill", "relax", "study", "coffee", "cozy"]):
        bpm = 82.0
        key = "A_minor"
        genre = "lofi"
        energy = "low"
    elif any(k in p for k in ["upbeat", "dance", "club", "energetic", "funky", "disco"]):
        bpm = 126.0
        key = "F_major"
        genre = "dance"
        energy = "high"
    elif any(k in p for k in ["cinematic", "epic", "orchestral", "dramatic", "trailer", "movie"]):
        bpm = 92.0
        key = "D_minor"
        genre = "cinematic"
        energy = "high"
    elif any(k in p for k in ["corporate", "presentation", "tech", "tutorial", "explainer", "motivating"]):
        bpm = 118.0
        key = "G_major"
        genre = "corporate"
        energy = "medium"
    elif any(k in p for k in ["ambient", "meditation", "peaceful", "calm", "zen", "drone"]):
        bpm = 65.0
        key = "E_minor"
        genre = "ambient"
        energy = "low"
    elif any(k in p for k in ["synthwave", "retrowave", "80s", "cyberpunk", "retro"]):
        bpm = 120.0
        key = "C_minor"
        genre = "synthwave"
        energy = "high"
        
    # Check if explicit BPM was written in prompt, e.g. "128 bpm" or "bpm: 120"
    bpm_match = re.search(r'(\d{2,3})\s*(?:bpm|tempo)', p)
    if bpm_match:
        found_bpm = float(bpm_match.group(1))
        if 40.0 <= found_bpm <= 240.0:
            bpm = found_bpm
            
    # Check if explicit key was written in prompt, e.g. "key of D minor", "C# major"
    key_match = re.search(r'(?:in|key(?:\s*of)?)\s*([a-g][#b]?)\s*(major|minor)', p)
    if key_match:
        root_k = key_match.group(1).capitalize()
        mode_k = key_match.group(2).lower()
        key = f"{root_k}_{mode_k}"
        
    return {
        "bpm": bpm,
        "key": key,
        "genre": genre,
        "energy": energy
    }

def parse_key_signature(key_str: str) -> Tuple[int, str]:
    """Parse key string like 'C_major' or 'A_minor' into (root_pitch, mode)."""
    cleaned = key_str.upper().replace("-", "_").replace(" ", "_")
    parts = cleaned.split("_")
    root_str = parts[0]
    mode = "major" if len(parts) < 2 or "MAJ" in parts[1] else "minor"
    
    root_midi = ROOT_PITCHES.get(root_str, 36)
    return root_midi, mode

def get_chord_progression(root_midi: int, mode: str, progression_index: int = 0) -> List[Dict[str, Any]]:
    """Return a sequence of chords with root and MIDI note voicings."""
    progs = PROGRESSIONS.get(mode, PROGRESSIONS["major"])
    prog = progs[progression_index % len(progs)]
    scale_ints = SCALE_INTERVALS.get(mode, SCALE_INTERVALS["major"])
    
    chord_list = []
    for deg in prog:
        chord_root = root_midi + deg
        # Form triad or 7th chord in the octave 4 (60+)
        # Voicing: root (octave 4), third, fifth, optional seventh
        c_root_oct4 = (chord_root % 12) + 60
        third_int = 4 if mode == "major" and deg in [0, 5, 7] else 3
        fifth_int = 7
        seventh_int = 11 if mode == "major" and deg in [0, 5] else 10
        
        chord_notes = [
            c_root_oct4,
            c_root_oct4 + third_int,
            c_root_oct4 + fifth_int,
            c_root_oct4 + seventh_int
        ]
        chord_list.append({
            "root": chord_root,
            "root_name": list(ROOT_PITCHES.keys())[list(ROOT_PITCHES.values()).index(chord_root % 12 + 36)],
            "notes": chord_notes
        })
    return chord_list

def calculate_sections(duration: float, user_sections: Optional[List[MusicalSection]], bpm: float) -> List[MusicalSection]:
    """Compute exact timing and bar indices for musical sections."""
    seconds_per_beat = 60.0 / bpm
    seconds_per_bar = seconds_per_beat * 4.0
    
    if user_sections and len(user_sections) > 0:
        # Scale/normalize user sections to match total duration exactly
        total_user_dur = sum(s.duration for s in user_sections)
        scale = duration / max(0.001, total_user_dur)
        
        cur_t = 0.0
        built_sections = []
        for s in user_sections:
            sec_dur = s.duration * scale
            start_b = int(cur_t / seconds_per_bar)
            end_b = int((cur_t + sec_dur) / seconds_per_bar)
            built_sections.append(MusicalSection(
                name=s.name.lower(),
                duration=sec_dur,
                start_time=round(cur_t, 3),
                end_time=round(cur_t + sec_dur, 3),
                start_bar=start_b,
                end_bar=end_b
            ))
            cur_t += sec_dur
        # Fix exact float rounding on last section
        built_sections[-1].end_time = duration
        built_sections[-1].duration = duration - built_sections[-1].start_time
        return built_sections
        
    # Auto-generate sections based on duration
    if duration <= 8.0:
        sec_configs = [
            ("intro", 0.25 * duration),
            ("main", 0.50 * duration),
            ("outro", 0.25 * duration)
        ]
    elif duration <= 24.0:
        sec_configs = [
            ("intro", 0.20 * duration),
            ("verse", 0.30 * duration),
            ("chorus", 0.30 * duration),
            ("outro", 0.20 * duration)
        ]
    elif duration <= 60.0:
        sec_configs = [
            ("intro", 0.15 * duration),
            ("verse_1", 0.25 * duration),
            ("chorus_1", 0.25 * duration),
            ("verse_2", 0.20 * duration),
            ("outro", 0.15 * duration)
        ]
    else:
        sec_configs = [
            ("intro", 0.10 * duration),
            ("verse_1", 0.20 * duration),
            ("chorus_1", 0.25 * duration),
            ("bridge", 0.15 * duration),
            ("chorus_2", 0.20 * duration),
            ("outro", 0.10 * duration)
        ]
        
    built = []
    cur_t = 0.0
    for name, dur in sec_configs:
        start_b = int(cur_t / seconds_per_bar)
        end_b = int((cur_t + dur) / seconds_per_bar)
        built.append(MusicalSection(
            name=name,
            duration=round(dur, 3),
            start_time=round(cur_t, 3),
            end_time=round(cur_t + dur, 3),
            start_bar=start_b,
            end_bar=end_b
        ))
        cur_t += dur
        
    built[-1].end_time = duration
    built[-1].duration = duration - built[-1].start_time
    return built
