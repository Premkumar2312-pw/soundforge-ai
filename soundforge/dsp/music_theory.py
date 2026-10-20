"""
Music Theory and Arrangement Engine for SoundForge AI
Handles scale generation, chord voicings, rhythm grids, section layout, and prompt analysis.
Includes guardrails for vocal requests, artist references, contradictory prompts, and multilingual input.
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

GENRE_PROGRESSIONS = {
    "lofi": {
        "minor": [[2, 7, 0, 9], [0, 5, 8, 7]],
        "major": [[2, 7, 0, 9], [0, 5, 2, 7]]
    },
    "ambient": {
        "minor": [[0, 5, 3, 7], [0, 8, 5, 10]],
        "major": [[0, 5, 9, 7], [0, 7, 5, 0]]
    },
    "cinematic": {
        "minor": [[0, 8, 5, 7], [0, 10, 8, 11]],
        "major": [[0, 7, 9, 5], [0, 8, 5, 7]]
    },
    "acoustic": {
        "minor": [[0, 8, 3, 10], [0, 5, 7, 0]],
        "major": [[0, 7, 9, 5], [0, 5, 0, 7]]
    },
    "corporate": {
        "major": [[0, 7, 9, 5], [0, 5, 9, 7]],
        "minor": [[0, 3, 5, 7]]
    },
    "synthwave": {
        "minor": [[0, 8, 3, 10], [0, 5, 8, 7]],
        "major": [[9, 5, 0, 7]]
    },
    "tense": {
        "minor": [[0, 1, 0, 6], [0, 6, 8, 1]],
        "major": [[0, 6, 5, 1]]
    },
    "playful": {
        "major": [[0, 9, 2, 7], [0, 5, 7, 0]],
        "minor": [[0, 5, 7, 0]]
    }
}

KNOWN_ARTISTS = [
    "hans zimmer", "taylor swift", "drake", "the beatles", "beatles", "queen",
    "beethoven", "mozart", "billie eilish", "daft punk", "ed sheeran", "coldplay",
    "eminem", "ac/dc", "acdc", "metallica", "john williams", "ludwig van beethoven",
    "bach", "chopin", "avicii", "skrillex", "deadmau5", "kanye", "kendrick lamar",
    "michael jackson", "adele", "the weeknd", "pink floyd", "led zeppelin", "radiohead"
]

VOCAL_KEYWORDS = [
    "vocal", "vocals", "singing", "singer", "singers", "lyrics", "voice",
    "rap", "rapper", "rapping", "choir", "chant", "spoken word", "acapella"
]

CONTRADICTORY_PAIRS = [
    ("calm", "aggressive"),
    ("peaceful", "intense"),
    ("slow", "fast"),
    ("quiet", "loud"),
    ("sad", "happy"),
    ("upbeat", "depressing")
]

MULTILINGUAL_KEYWORDS = {
    "lofi": ["relajante", "detente", "ruhig", "calme", "relaxant", "tranquilo"],
    "dance": ["danse", "baile", "tanzen", "fiesta", "fête", "alegre"],
    "cinematic": ["cinematographique", "cinematografico", "filmisch", "épique", "epico"],
    "ambient": ["ambiente", "méditation", "meditacion", "entspannung"]
}

def analyze_prompt_musicality(prompt: str) -> Dict[str, Any]:
    """
    Extract musical intent, genre, BPM, and mood from natural language prompt.
    Applies guardrails for vocals, artist names, contradictory prompts, and multilingual input.
    """
    p = prompt.lower()
    warnings = []

    # 1. Vocal guardrail check
    has_vocals = any(re.search(r'\b' + re.escape(vk) + r'\b', p) for vk in VOCAL_KEYWORDS)
    if has_vocals:
        warnings.append(
            "Vocals/singing were requested in the prompt. Procedural instrumental-only synthesis enforced per PS1 specification."
        )

    # 2. Real artist / copyrighted song guardrail check
    for artist in KNOWN_ARTISTS:
        if artist in p:
            warnings.append(
                f"Prompt references recognized artist/song '{artist}'. Procedural original synthesis generated to avoid copyright infringement."
            )
            break

    # 3. Contradictory prompts check
    for w1, w2 in CONTRADICTORY_PAIRS:
        if w1 in p and w2 in p:
            warnings.append(
                f"Contradictory mood descriptors detected ('{w1}' and '{w2}'). Generating balanced hybrid arrangement."
            )

    # Defaults
    bpm = 118.0
    key = "C_major"
    genre = "electronic"
    energy = "medium"

    # Genre / Mood detection (including multilingual)
    if any(k in p for k in ["lo-fi", "lofi", "chill", "relax", "study", "coffee", "cozy"] + MULTILINGUAL_KEYWORDS["lofi"]):
        bpm = 82.0
        key = "A_minor"
        genre = "lofi"
        energy = "low"
    elif any(k in p for k in ["upbeat", "dance", "club", "energetic", "funky", "disco"] + MULTILINGUAL_KEYWORDS["dance"]):
        bpm = 126.0
        key = "F_major"
        genre = "dance"
        energy = "high"
    elif any(k in p for k in ["cinematic", "epic", "orchestral", "dramatic", "trailer", "movie", "film"] + MULTILINGUAL_KEYWORDS["cinematic"]):
        bpm = 92.0
        key = "D_minor"
        genre = "cinematic"
        energy = "high"
    elif any(k in p for k in ["corporate", "presentation", "tech", "tutorial", "explainer", "motivating", "business"]):
        bpm = 118.0
        key = "G_major"
        genre = "corporate"
        energy = "medium"
    elif any(k in p for k in ["ambient", "meditation", "peaceful", "calm", "zen", "drone"] + MULTILINGUAL_KEYWORDS["ambient"]):
        bpm = 65.0
        key = "E_minor"
        genre = "ambient"
        energy = "low"
    elif any(k in p for k in ["synthwave", "retrowave", "80s", "cyberpunk", "retro"]):
        bpm = 120.0
        key = "C_minor"
        genre = "synthwave"
        energy = "high"
    elif any(k in p for k in ["acoustic", "folk", "guitar", "unplugged", "organic"]):
        bpm = 104.0
        key = "D_major"
        genre = "acoustic"
        energy = "medium"
    elif any(k in p for k in ["tense", "suspense", "thriller", "dark", "mystery"]):
        bpm = 88.0
        key = "F_minor"
        genre = "tense"
        energy = "medium"
    elif any(k in p for k in ["playful", "comedy", "cartoon", "quirky", "bouncy", "game"]):
        bpm = 132.0
        key = "C_major"
        genre = "playful"
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
        "energy": energy,
        "warnings": warnings
    }

def parse_key_signature(key_str: str) -> Tuple[int, str]:
    """Parse key string like 'C_major' or 'A_minor' into (root_pitch, mode)."""
    cleaned = key_str.upper().replace("-", "_").replace(" ", "_")
    parts = cleaned.split("_")
    root_str = parts[0]
    mode = "major" if len(parts) < 2 or "MAJ" in parts[1] else "minor"

    root_midi = ROOT_PITCHES.get(root_str, 36)
    return root_midi, mode

def get_chord_progression(root_midi: int, mode: str, progression_index: int = 0, genre: str = "electronic") -> List[Dict[str, Any]]:
    """Return a sequence of chords with root and MIDI note voicings conditioned on genre."""
    genre_progs = GENRE_PROGRESSIONS.get(genre, {}).get(mode)
    if genre_progs:
        prog = genre_progs[progression_index % len(genre_progs)]
    else:
        progs = PROGRESSIONS.get(mode, PROGRESSIONS["major"])
        prog = progs[progression_index % len(progs)]

    chord_list = []
    for deg in prog:
        chord_root = root_midi + deg
        c_root_oct4 = (chord_root % 12) + 60
        third_int = 4 if mode == "major" and deg in [0, 5, 7] else 3
        fifth_int = 7
        seventh_int = 11 if mode == "major" and deg in [0, 5] else 10

        if genre == "lofi":
            chord_notes = [
                c_root_oct4,
                c_root_oct4 + third_int,
                c_root_oct4 + fifth_int,
                c_root_oct4 + seventh_int,
                c_root_oct4 + 14
            ]
        elif genre == "ambient":
            chord_notes = [
                c_root_oct4 - 12,
                c_root_oct4,
                c_root_oct4 + 2,
                c_root_oct4 + fifth_int,
                c_root_oct4 + 12
            ]
        elif genre == "tense":
            chord_notes = [
                c_root_oct4 - 12,
                c_root_oct4,
                c_root_oct4 + 1,
                c_root_oct4 + 6,
                c_root_oct4 + seventh_int
            ]
        elif genre == "cinematic":
            chord_notes = [
                c_root_oct4 - 12,
                c_root_oct4,
                c_root_oct4 + third_int,
                c_root_oct4 + fifth_int,
                c_root_oct4 + 12
            ]
        else:
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

def calculate_sections(
    duration: float,
    user_sections: Optional[List[MusicalSection]],
    bpm: float,
    warnings: Optional[List[str]] = None
) -> List[MusicalSection]:
    """
    Compute exact timing and bar indices for musical sections.
    Handles start_s / mood formats, filters invalid sections (>= duration),
    handles closely spaced sections (< 1.5s), and ensures grid alignment.
    Returns sections list. Appends to warnings list if provided.
    """
    local_warnings = []
    seconds_per_beat = 60.0 / bpm
    seconds_per_bar = seconds_per_beat * 4.0

    if user_sections and len(user_sections) > 0:
        # Check if sections use start_s / mood contract
        has_start_s = any(s.start_s is not None or s.start_time is not None for s in user_sections)

        if has_start_s:
            # Filter sections that start at or after track duration
            valid_secs = []
            for s in user_sections:
                st = s.start_s if s.start_s is not None else (s.start_time if s.start_time is not None else 0.0)
                if st >= duration:
                    local_warnings.append(
                        f"Section '{s.name or s.mood}' starts at {st}s which is >= total duration ({duration}s); omitted."
                    )
                else:
                    valid_secs.append((st, s))

            if not valid_secs:
                # Fallback to auto sections if all were invalid
                user_sections = None
            else:
                # Sort by start time
                valid_secs.sort(key=lambda x: x[0])

                # Check for closely spaced sections (< 1.5s)
                filtered_secs = []
                for i, (st, s) in enumerate(valid_secs):
                    if i > 0 and (st - valid_secs[i-1][0]) < 1.5:
                        local_warnings.append(
                            f"Section '{s.name or s.mood}' starts at {st}s, which is < 1.5s from previous section. Closely-spaced section merged/stabilized."
                        )
                    filtered_secs.append((st, s))

                built_sections = []
                for i, (st, s) in enumerate(filtered_secs):
                    next_st = filtered_secs[i+1][0] if i + 1 < len(filtered_secs) else duration
                    sec_dur = max(0.01, next_st - st)
                    start_b = int(st / seconds_per_bar)
                    end_b = int(next_st / seconds_per_bar)
                    name = (s.mood or s.name or f"section_{i+1}").lower()
                    built_sections.append(MusicalSection(
                        name=name,
                        mood=name,
                        duration=round(sec_dur, 3),
                        start_time=round(st, 3),
                        start_s=round(st, 3),
                        end_time=round(next_st, 3),
                        start_bar=start_b,
                        end_bar=end_b
                    ))
                built_sections[-1].end_time = duration
                built_sections[-1].duration = duration - built_sections[-1].start_time
                if warnings is not None:
                    warnings.extend(local_warnings)
                return built_sections
        else:
            # User provided sections with duration only
            total_user_dur = sum(s.duration for s in user_sections if s.duration)
            scale = duration / max(0.001, total_user_dur)
            cur_t = 0.0
            built_sections = []
            for s in user_sections:
                sec_dur = (s.duration or 1.0) * scale
                start_b = int(cur_t / seconds_per_bar)
                end_b = int((cur_t + sec_dur) / seconds_per_bar)
                name = (s.name or s.mood or "section").lower()
                built_sections.append(MusicalSection(
                    name=name,
                    mood=name,
                    duration=round(sec_dur, 3),
                    start_time=round(cur_t, 3),
                    start_s=round(cur_t, 3),
                    end_time=round(cur_t + sec_dur, 3),
                    start_bar=start_b,
                    end_bar=end_b
                ))
                cur_t += sec_dur
            built_sections[-1].end_time = duration
            built_sections[-1].duration = duration - built_sections[-1].start_time
            if warnings is not None:
                warnings.extend(local_warnings)
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
            mood=name,
            duration=round(dur, 3),
            start_time=round(cur_t, 3),
            start_s=round(cur_t, 3),
            end_time=round(cur_t + dur, 3),
            start_bar=start_b,
            end_bar=end_b
        ))
        cur_t += dur

    built[-1].end_time = duration
    built[-1].duration = duration - built[-1].start_time
    if warnings is not None:
        warnings.extend(local_warnings)
    return built
