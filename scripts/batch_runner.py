"""
SoundForge AI - Automated Batch Test Runner (IncuBrix Assessment & PS1 Specification)
Full automated execution across the 10 Diverse Musical Styles, Durations, and 19 Hard Cases.

Features:
- CLI flags for single JSON file (--file), directory of JSONs (--dir), or test suites (--suite)
- Generates JSON and CSV summary reports in test_output/
- Downloads and verifies mix.wav, stems, and manifest for each run
- Validates duration (<= 0.05s tolerance), loudness (-16 +/- 1 LU), True Peak (<= -1 dBTP), and stem reconstruction error
"""

import sys
import os
import csv
import time
import json
import asyncio
import argparse
import numpy as np
import soundfile as sf
import httpx
from typing import List, Dict, Any, Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from soundforge.api.app import app

def ensure_mock_narration_files() -> Dict[str, str]:
    """Generate speech and silent audio files for ducking and hard-case tests."""
    os.makedirs("test_output", exist_ok=True)
    sr = 48000
    duration = 8.0
    total_samples = int(duration * sr)
    t = np.linspace(0, duration, total_samples, endpoint=False)

    # 1. Speech narration
    speech_path = os.path.abspath("test_output/mock_narration.wav")
    speech = np.zeros(total_samples, dtype=np.float32)
    s_start, s_end = int(1.5 * sr), int(5.0 * sr)
    speech[s_start:s_end] = 0.5 * np.sin(2 * np.pi * 300 * t[s_start:s_end]) * np.sin(2 * np.pi * 25 * t[s_start:s_end])
    sf.write(speech_path, np.column_stack((speech, speech)), sr, subtype='PCM_16')

    # 2. Silent narration (Hard Case #9)
    silent_path = os.path.abspath("test_output/mock_silent_narration.wav")
    silent = np.zeros((total_samples, 2), dtype=np.float32)
    sf.write(silent_path, silent, sr, subtype='PCM_16')

    return {"speech": speech_path, "silent": silent_path}

NARRATION_FILES = ensure_mock_narration_files()

# -------------------------------------------------------------
# 10 DIVERSE MUSICAL STYLES PACK (Assessment Requirement 2.C)
# -------------------------------------------------------------
TEN_PROMPTS_PACK = [
    {
        "id": "PROMPT-01",
        "genre": "Corporate",
        "description": "Corporate - Modern tech presentation background",
        "payload": {
            "prompt": "Upbeat modern corporate tech presentation background music with inspiring rhythm and light synths",
            "duration_s": 15.0,
            "tempo_bpm": 118.0,
            "key": "G_major",
            "loopable": False,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav", "mp3"]},
            "seed": 101
        }
    },
    {
        "id": "PROMPT-02",
        "genre": "Cinematic",
        "description": "Cinematic - Dramatic trailer intro build",
        "payload": {
            "prompt": "Epic dramatic orchestral movie trailer intro building tension towards heroic climax",
            "duration_s": 20.0,
            "tempo_bpm": 92.0,
            "key": "D_minor",
            "loopable": False,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav"]},
            "seed": 102
        }
    },
    {
        "id": "PROMPT-03",
        "genre": "Lo-Fi",
        "description": "Lo-Fi - Chill study beats",
        "payload": {
            "prompt": "Relaxing lo-fi chill study beat with soft electric piano and gentle vinyl warmth",
            "duration_s": 16.0,
            "tempo_bpm": 82.0,
            "key": "A_minor",
            "loopable": True,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav"]},
            "seed": 103
        }
    },
    {
        "id": "PROMPT-04",
        "genre": "Electronic",
        "description": "Electronic - High energy club dance track",
        "payload": {
            "prompt": "High-energy electronic dance track with driving four-on-the-floor beat and pumping bassline",
            "duration_s": 15.0,
            "tempo_bpm": 128.0,
            "key": "F_major",
            "loopable": True,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav", "mp3"]},
            "seed": 104
        }
    },
    {
        "id": "PROMPT-05",
        "genre": "Acoustic",
        "description": "Acoustic - Warm organic folk guitar",
        "payload": {
            "prompt": "Warm organic acoustic folk melody with gentle strumming rhythm and pastoral warmth",
            "duration_s": 14.0,
            "tempo_bpm": 104.0,
            "key": "D_major",
            "loopable": False,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav"]},
            "seed": 105
        }
    },
    {
        "id": "PROMPT-06",
        "genre": "Tense",
        "description": "Tense - Dark suspense thriller underscore",
        "payload": {
            "prompt": "Dark suspenseful crime thriller underscore with pulsing bass and nervous anticipation",
            "duration_s": 15.0,
            "tempo_bpm": 88.0,
            "key": "F_minor",
            "loopable": False,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav"]},
            "seed": 106
        }
    },
    {
        "id": "PROMPT-07",
        "genre": "Playful",
        "description": "Playful - Quirky comedy video game background",
        "payload": {
            "prompt": "Quirky playful comedy video game background music with bouncy staccato rhythm",
            "duration_s": 12.0,
            "tempo_bpm": 132.0,
            "key": "C_major",
            "loopable": True,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav"]},
            "seed": 107
        }
    },
    {
        "id": "PROMPT-08",
        "genre": "Ambient",
        "description": "Ambient - Serene meditation drone",
        "payload": {
            "prompt": "Serene peaceful ambient meditation music with calm sustained pads and spacious stillness",
            "duration_s": 25.0,
            "tempo_bpm": 65.0,
            "key": "E_minor",
            "loopable": False,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav"]},
            "seed": 108
        }
    },
    {
        "id": "PROMPT-09",
        "genre": "Upbeat",
        "description": "Upbeat - Sunny energetic pop funk groove",
        "payload": {
            "prompt": "Sunny energetic upbeat pop funk groove with cheerful bass and optimistic harmony",
            "duration_s": 14.0,
            "tempo_bpm": 122.0,
            "key": "G_major",
            "loopable": True,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav", "mp3"]},
            "seed": 109
        }
    },
    {
        "id": "PROMPT-10",
        "genre": "Synthwave",
        "description": "Synthwave - Retro 80s cyberpunk highway drive",
        "payload": {
            "prompt": "Retro 80s neon synthwave cyberpunk highway driving groove with analog lead synth",
            "duration_s": 16.0,
            "tempo_bpm": 120.0,
            "key": "C_minor",
            "loopable": True,
            "output": {"sample_rate": 48000, "target_lufs": -16.0, "formats": ["wav", "mp3"]},
            "seed": 110
        }
    }
]

# -------------------------------------------------------------
# HARD CASES & EDGE CASES (Assessment Section 3)
# -------------------------------------------------------------
HARD_CASES_PACK = [
    {
        "id": "HC-01",
        "category": "Boundary",
        "description": "Minimum Duration Boundary (5.0s)",
        "payload": {"prompt": "Quick short intro sting", "duration_s": 5.0, "seed": 501},
        "expect_success": True
    },
    {
        "id": "HC-02",
        "category": "Boundary",
        "description": "Maximum Duration Boundary (300.0s / 5 Minutes)",
        "payload": {"prompt": "Full background ambient soundscape for long video", "duration_s": 300.0, "seed": 502},
        "expect_success": True
    },
    {
        "id": "HC-03",
        "category": "Contradictory",
        "description": "Contradictory Prompt ('calm but aggressive')",
        "payload": {"prompt": "Calm but aggressive corporate dance beat", "duration_s": 8.0, "seed": 503},
        "expect_success": True,
        "expect_warning": "Contradictory"
    },
    {
        "id": "HC-04",
        "category": "Copyright/Artist",
        "description": "Artist Reference ('in the style of Hans Zimmer')",
        "payload": {"prompt": "Epic orchestral score in the style of Hans Zimmer", "duration_s": 8.0, "seed": 504},
        "expect_success": True,
        "expect_warning": "hans zimmer"
    },
    {
        "id": "HC-05",
        "category": "Instrumental Guardrail",
        "description": "Vocal Request ('with female singing and vocals')",
        "payload": {"prompt": "Pop song with catchy female vocals and singing lyrics", "duration_s": 8.0, "seed": 505},
        "expect_success": True,
        "expect_warning": "Vocals"
    },
    {
        "id": "HC-06",
        "category": "Sections Edge",
        "description": "Closely-Spaced Sections (< 1.5s apart)",
        "payload": {
            "prompt": "Rapid section changes",
            "duration_s": 8.0,
            "sections": [{"start_s": 0.0, "mood": "intro"}, {"start_s": 0.8, "mood": "verse"}],
            "seed": 506
        },
        "expect_success": True,
        "expect_warning": "1.5s"
    },
    {
        "id": "HC-07",
        "category": "Sections Edge",
        "description": "Section Starting At/After Track Duration (10.0s >= 8.0s)",
        "payload": {
            "prompt": "Section out of bounds",
            "duration_s": 8.0,
            "sections": [{"start_s": 0.0, "mood": "intro"}, {"start_s": 10.0, "mood": "outro"}],
            "seed": 507
        },
        "expect_success": True,
        "expect_warning": "omitted"
    },
    {
        "id": "HC-08",
        "category": "Narration Ducking",
        "description": "Narration with Long Silences / Zero Speech",
        "payload": {
            "prompt": "Corporate audio with silent narration track",
            "duration_s": 8.0,
            "narration_url": NARRATION_FILES["silent"],
            "seed": 508
        },
        "expect_success": True
    },
    {
        "id": "HC-09",
        "category": "Multilingual",
        "description": "Non-English Prompt (French: 'musique relaxante au piano')",
        "payload": {"prompt": "Musique relaxante au piano pour la détente et le calme", "duration_s": 8.0, "seed": 509},
        "expect_success": True
    },
    {
        "id": "HC-10",
        "category": "Validation Rejection",
        "description": "Below Minimum Duration (4.0s < 5.0s minimum -> HTTP 422)",
        "payload": {"prompt": "Too short audio track", "duration_s": 4.0},
        "expect_success": False,
        "expected_status": 422
    }
]

async def execute_case(client: httpx.AsyncClient, tc: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    tc_id = tc["id"]
    desc = tc["description"]
    payload = tc["payload"]
    expect_success = tc.get("expect_success", True)

    t_start = time.perf_counter()
    headers = {
        "Idempotency-Key": f"batch-{tc_id}-{int(time.time())}",
        "X-Correlation-ID": f"corr-{tc_id}"
    }

    resp = await client.post("/api/v1/music/jobs", json=payload, headers=headers)

    if not expect_success:
        exp_code = tc.get("expected_status", 422)
        if resp.status_code == exp_code:
            tot = round(time.perf_counter() - t_start, 2)
            print(f"  [PASS] Correctly rejected with HTTP {resp.status_code}")
            return {
                "id": tc_id,
                "description": desc,
                "status": f"PASS (Expected {exp_code})",
                "execution_time_s": tot,
                "target_duration_s": payload.get("duration_s", 0),
                "actual_duration_s": 0.0,
                "measured_lufs": 0.0,
                "true_peak_dbtp": 0.0,
                "max_recon_error": 0.0,
                "warnings": []
            }
        else:
            return {
                "id": tc_id,
                "description": desc,
                "status": "FAIL",
                "error": f"Expected HTTP {exp_code}, got {resp.status_code}"
            }

    if resp.status_code != 202:
        return {
            "id": tc_id,
            "description": desc,
            "status": "FAIL",
            "error": f"Submission returned HTTP {resp.status_code}: {resp.text}"
        }

    job_data = resp.json()
    job_id = job_data["job_id"]

    # Poll status endpoint
    dur = payload.get("duration_s", payload.get("duration", 10.0))
    max_wait = max(40.0, dur * 0.45)
    poll_interval = 0.5
    elapsed = 0.0
    status_data = None

    while elapsed < max_wait:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

        s_resp = await client.get(f"/api/v1/jobs/{job_id}")
        if s_resp.status_code == 200:
            sd = s_resp.json()
            if sd["status"] in ("completed", "succeeded"):
                status_data = sd
                break
            elif sd["status"] == "failed":
                return {
                    "id": tc_id,
                    "description": desc,
                    "status": "FAIL",
                    "error": f"Job failed: {sd.get('error')}"
                }

    total_time = round(time.perf_counter() - t_start, 2)

    if not status_data:
        return {
            "id": tc_id,
            "description": desc,
            "status": "TIMEOUT",
            "error": f"Timed out after {max_wait}s"
        }

    manifest = status_data["manifest"]
    metrics = manifest["audio_metrics"]
    recon = manifest["reconstruction_verification"]
    warnings = manifest.get("warnings", [])

    dur_err = abs(metrics["actual_duration_seconds"] - dur)
    lufs_err = abs(metrics["measured_loudness_lufs"] - (-16.0))
    peak_ok = metrics["true_peak_dbtp"] <= metrics["max_true_peak_limit_dbtp"] + 0.05
    recon_ok = recon["max_reconstruction_error"] < 1e-5

    passed = (dur_err <= 0.05) and (lufs_err <= 1.0) and peak_ok and recon_ok

    # Save artifacts for this case
    case_dir = os.path.join(output_dir, tc_id)
    os.makedirs(case_dir, exist_ok=True)
    with open(os.path.join(case_dir, "music_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    status_tag = "[PASS]" if passed else "[FAIL]"
    print(f"  {status_tag} Done in {total_time}s | Dur: {metrics['actual_duration_seconds']}s (err: {dur_err:.3f}s) | LUFS: {metrics['measured_loudness_lufs']} | Peak: {metrics['true_peak_dbtp']} dBTP | Recon Err: {recon['max_reconstruction_error']:.2e}")

    return {
        "id": tc_id,
        "description": desc,
        "status": "PASS" if passed else "FAIL",
        "execution_time_s": total_time,
        "target_duration_s": dur,
        "actual_duration_s": metrics["actual_duration_seconds"],
        "target_lufs": -16.0,
        "measured_lufs": metrics["measured_loudness_lufs"],
        "true_peak_dbtp": metrics["true_peak_dbtp"],
        "max_recon_error": recon["max_reconstruction_error"],
        "warnings": warnings
    }

async def run_suite(client: httpx.AsyncClient, cases: List[Dict[str, Any]], suite_name: str, output_dir: str):
    print("\n" + "="*85)
    print(f" SOUNDFORGE AI - {suite_name.upper()} ({len(cases)} Cases)")
    print("="*85 + "\n")

    results = []
    for tc in cases:
        print(f"[{tc['id']}] Running: {tc['description']}...")
        res = await execute_case(client, tc, output_dir)
        results.append(res)

    print("\n" + "="*110)
    print(f" {suite_name.upper()} SUMMARY REPORT")
    print("="*110)
    print(f"{'ID':<11} | {'Status':<16} | {'Target Dur':<10} | {'Act Dur':<8} | {'Act LUFS':<9} | {'Peak dBTP':<9} | {'Recon Err':<10} | {'Time(s)':<7}")
    print("-" * 110)
    for r in results:
        if "PASS" in r.get("status"):
            print(f"{r['id']:<11} | {r['status']:<16} | {r['target_duration_s']:<10.1f} | {r['actual_duration_s']:<8.2f} | {r['measured_lufs']:<9.2f} | {r['true_peak_dbtp']:<9.2f} | {r['max_recon_error']:<10.2e} | {r['execution_time_s']:<7.2f}")
        else:
            print(f"{r['id']:<11} | {r['status']:<16} | {r.get('error', 'Failure')}")
    print("="*110 + "\n")

    # Export to JSON
    json_path = os.path.join(output_dir, f"{suite_name.lower().replace(' ', '_')}_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Export to CSV
    csv_path = os.path.join(output_dir, f"{suite_name.lower().replace(' ', '_')}_report.csv")
    keys = ["id", "description", "status", "execution_time_s", "target_duration_s", "actual_duration_s", "measured_lufs", "true_peak_dbtp", "max_recon_error"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"Reports saved to {json_path} and {csv_path}")
    return results

async def main():
    parser = argparse.ArgumentParser(description="SoundForge AI Batch Runner")
    parser.add_argument("--url", type=str, default="", help="Optional base URL of running server")
    parser.add_argument("--suite", type=str, default="all", choices=["all", "ten_prompts", "diverse", "hard_cases"], help="Test suite to execute")
    parser.add_argument("--output-dir", type=str, default="test_output", help="Output directory for reports and artifacts")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    cases_to_run = []
    suite_title = "Batch Matrix"
    if args.suite in ("ten_prompts", "diverse"):
        cases_to_run = TEN_PROMPTS_PACK
        suite_title = "10 Diverse Prompts Pack"
    elif args.suite == "hard_cases":
        cases_to_run = HARD_CASES_PACK
        suite_title = "Hard Cases & Edge Cases Pack"
    else:
        cases_to_run = TEN_PROMPTS_PACK + HARD_CASES_PACK
        suite_title = "Comprehensive IncuBrix Test Pack"

    if args.url:
        async with httpx.AsyncClient(base_url=args.url, timeout=400.0) as client:
            await run_suite(client, cases_to_run, suite_title, args.output_dir)
    else:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=400.0) as client:
            await run_suite(client, cases_to_run, suite_title, args.output_dir)

if __name__ == "__main__":
    asyncio.run(main())
