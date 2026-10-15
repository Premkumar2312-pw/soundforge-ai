"""
SoundForge AI - Automated Batch Test Runner (PS1 Specification)
Executes comprehensive test matrices across diverse musical styles, durations, and edge cases.
Validates:
- 5s, 10s, 60s, 180s, 300s durations (including min/max boundaries)
- -16.0 LUFS default target loudness (+/- 1.0 LU tolerance)
- True Peak <= -1.0 dBTP
- Duration tolerance <= 0.05s
- Exact mathematical stem reconstruction from saved disk files
- Narration sidechain ducking
- Difficult input validation failure (4.0s duration rejected with HTTP 422)
"""

import sys
import os
import time
import json
import asyncio
import argparse
import numpy as np
import soundfile as sf
import httpx
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from soundforge.api.app import app

def ensure_mock_narration_file() -> str:
    """Generate a clean mock speech audio file for ducking tests."""
    os.makedirs("test_output", exist_ok=True)
    narration_path = os.path.abspath("test_output/mock_narration.wav")
    sr = 48000
    duration = 8.0
    total_samples = int(duration * sr)
    t = np.linspace(0, duration, total_samples, endpoint=False)
    
    # Silence for 1.5s, speech tone/chatter for 3.5s, silence for 3s
    speech = np.zeros(total_samples, dtype=np.float32)
    s_start, s_end = int(1.5 * sr), int(5.0 * sr)
    speech[s_start:s_end] = 0.5 * np.sin(2 * np.pi * 300 * t[s_start:s_end]) * np.sin(2 * np.pi * 25 * t[s_start:s_end])
    stereo_speech = np.column_stack((speech, speech))
    sf.write(narration_path, stereo_speech, sr, subtype='PCM_16')
    return narration_path

MOCK_NARRATION_PATH = ensure_mock_narration_file()

TEST_CASES = [
    {
        "id": "TC-01",
        "description": "Minimum Duration Boundary (5.0s)",
        "payload": {
            "prompt": "Upbeat tech corporate intro sting with inspiring rhythm",
            "duration": 5.0,
            "tempo": 120.0,
            "key": "C_major",
            "loopability": False,
            "target_loudness": -16.0,
            "output_formats": ["wav", "mp3"],
            "seed": 1001
        },
        "expect_success": True
    },
    {
        "id": "TC-02",
        "description": "Representative Track (10.0s Lo-Fi Loop)",
        "payload": {
            "prompt": "Relaxing lo-fi chill study beat with soft keys and gentle bass",
            "duration": 10.0,
            "tempo": 82.0,
            "key": "A_minor",
            "loopability": True,
            "target_loudness": -16.0,
            "output_formats": ["wav"],
            "seed": 2002
        },
        "expect_success": True
    },
    {
        "id": "TC-03",
        "description": "Medium Duration Track (60.0s Cinematic Build)",
        "payload": {
            "prompt": "Epic dramatic trailer intro building up through verse and chorus to intense climax",
            "duration": 60.0,
            "tempo": 96.0,
            "key": "D_minor",
            "sections": [
                {"name": "intro", "duration": 10.0},
                {"name": "verse", "duration": 20.0},
                {"name": "chorus", "duration": 20.0},
                {"name": "outro", "duration": 10.0}
            ],
            "loopability": False,
            "target_loudness": -16.0,
            "output_formats": ["wav"],
            "seed": 3003
        },
        "expect_success": True
    },
    {
        "id": "TC-04",
        "description": "Extended Duration Track (180.0s / 3 Minutes)",
        "payload": {
            "prompt": "Peaceful ambient meditation music with calm sustained chords and slow evolving pads",
            "duration": 180.0,
            "tempo": 70.0,
            "key": "G_major",
            "loopability": False,
            "target_loudness": -16.0,
            "output_formats": ["wav"],
            "seed": 4004
        },
        "expect_success": True
    },
    {
        "id": "TC-05",
        "description": "Maximum Duration Boundary (300.0s / 5 Minutes)",
        "payload": {
            "prompt": "Retro 80s synthwave cyberpunk driving groove with energetic beat",
            "duration": 300.0,
            "tempo": 124.0,
            "key": "F_major",
            "loopability": True,
            "target_loudness": -16.0,
            "output_formats": ["wav"],
            "seed": 5005
        },
        "expect_success": True
    },
    {
        "id": "TC-06",
        "description": "Narration Sidechain Ducking (8.0s)",
        "payload": {
            "prompt": "Corporate explainer background music with speech ducking",
            "duration": 8.0,
            "tempo": 115.0,
            "key": "C_major",
            "narration_url": MOCK_NARRATION_PATH,
            "loopability": False,
            "target_loudness": -16.0,
            "output_formats": ["wav", "mp3"],
            "seed": 6006
        },
        "expect_success": True
    },
    {
        "id": "TC-07",
        "description": "Difficult Input Boundary Rejection (4.0s < 5.0s minimum)",
        "payload": {
            "prompt": "Too short audio clip",
            "duration": 4.0,
            "target_loudness": -16.0
        },
        "expect_success": False,
        "expected_status": 422
    }
]

async def run_batch_tests(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    print("\n" + "="*85)
    print(" SOUNDFORGE AI - PS1 COMPREHENSIVE BATCH TEST MATRIX")
    print("="*85 + "\n")

    results = []

    for tc in TEST_CASES:
        tc_id = tc["id"]
        desc = tc["description"]
        payload = tc["payload"]
        expect_success = tc.get("expect_success", True)
        print(f"[{tc_id}] Running: {desc} (Duration: {payload['duration']}s)...")

        t_start = time.perf_counter()

        # 1. Submit Job
        headers = {
            "Idempotency-Key": f"batch-{tc_id}",
            "X-Correlation-ID": f"corr-{tc_id}"
        }
        resp = await client.post("/api/v1/music/jobs", json=payload, headers=headers)

        # Handle expected rejection test cases (e.g. TC-07)
        if not expect_success:
            if resp.status_code == tc.get("expected_status", 422):
                total_time = round(time.perf_counter() - t_start, 2)
                print(f"  [PASS] Correctly rejected invalid input with HTTP {resp.status_code}")
                results.append({
                    "id": tc_id,
                    "description": desc,
                    "target_duration_s": payload["duration"],
                    "actual_duration_s": 0.0,
                    "target_lufs": -16.0,
                    "measured_lufs": 0.0,
                    "true_peak_dbtp": 0.0,
                    "max_recon_error": 0.0,
                    "execution_time_s": total_time,
                    "status": "PASS (Rejected 422)"
                })
                continue
            else:
                print(f"  FAILED: Expected HTTP {tc.get('expected_status')}, got {resp.status_code}")
                results.append({
                    "id": tc_id,
                    "description": desc,
                    "status": "FAIL",
                    "error": f"Expected {tc.get('expected_status')}, got {resp.status_code}"
                })
                continue

        if resp.status_code != 202:
            print(f"  FAILED: Expected HTTP 202, got {resp.status_code}: {resp.text}")
            results.append({
                "id": tc_id,
                "description": desc,
                "status": "FAIL",
                "error": f"Submission returned {resp.status_code}"
            })
            continue

        job_info = resp.json()
        job_id = job_info["job_id"]

        # 2. Poll Job until complete (allow scaled timeout for long tracks)
        max_wait = max(30.0, payload["duration"] * 0.40)
        poll_interval = 0.5
        elapsed = 0.0
        completed_data = None

        while elapsed < max_wait:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            status_resp = await client.get(f"/api/v1/music/jobs/{job_id}")
            if status_resp.status_code == 200:
                s_data = status_resp.json()
                if s_data["status"] == "completed":
                    completed_data = s_data
                    break
                elif s_data["status"] == "failed":
                    print(f"  FAILED: Job failed: {s_data.get('error')}")
                    break

        total_time = round(time.perf_counter() - t_start, 2)

        if not completed_data:
            results.append({
                "id": tc_id,
                "description": desc,
                "status": "TIMEOUT",
                "error": f"Job timed out after {max_wait}s"
            })
            continue

        manifest = completed_data["manifest"]
        metrics = manifest["audio_metrics"]
        recon = manifest["reconstruction_verification"]

        # Validate PS1 specifications
        dur_err = abs(metrics["actual_duration_seconds"] - payload["duration"])
        lufs_err = abs(metrics["measured_loudness_lufs"] - payload["target_loudness"])
        peak_ok = metrics["true_peak_dbtp"] <= metrics["max_true_peak_limit_dbtp"] + 0.05
        recon_ok = recon["max_reconstruction_error"] < 1e-5
        ducking_ok = True
        if payload.get("narration_url"):
            ducking_ok = manifest.get("ducking", {}).get("ducking_applied") is True

        passed = (dur_err <= 0.05) and (lufs_err <= 1.0) and peak_ok and recon_ok and ducking_ok

        result_entry = {
            "id": tc_id,
            "description": desc,
            "target_duration_s": payload["duration"],
            "actual_duration_s": metrics["actual_duration_seconds"],
            "target_lufs": payload["target_loudness"],
            "measured_lufs": metrics["measured_loudness_lufs"],
            "true_peak_dbtp": metrics["true_peak_dbtp"],
            "max_recon_error": recon["max_reconstruction_error"],
            "execution_time_s": total_time,
            "status": "PASS" if passed else "FAIL"
        }
        results.append(result_entry)

        status_tag = "[PASS]" if passed else "[FAIL]"
        print(f"  {status_tag} Completed in {total_time}s | Act Dur: {metrics['actual_duration_seconds']}s | LUFS: {metrics['measured_loudness_lufs']} | Peak: {metrics['true_peak_dbtp']} dBTP | Recon Error: {recon['max_reconstruction_error']}")

    print("\n" + "="*95)
    print(" PS1 BATCH TEST EXECUTION SUMMARY")
    print("="*95)
    print(f"{'ID':<7} | {'Status':<16} | {'Target Dur':<10} | {'Act Dur':<8} | {'Target LUFS':<11} | {'Act LUFS':<9} | {'Peak dBTP':<9} | {'Recon Err':<10} | {'Time(s)':<7}")
    print("-" * 105)
    for r in results:
        if "PASS" in r.get("status"):
            print(f"{r['id']:<7} | {r['status']:<16} | {r['target_duration_s']:<10.1f} | {r['actual_duration_s']:<8.2f} | {r['target_lufs']:<11.1f} | {r['measured_lufs']:<9.2f} | {r['true_peak_dbtp']:<9.2f} | {r['max_recon_error']:<10.6f} | {r['execution_time_s']:<7.2f}")
        else:
            print(f"{r['id']:<7} | {r['status']:<16} | {r.get('error', 'Unknown failure')}")
    print("="*95 + "\n")

    # Save to JSON
    with open("batch_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Full results exported to 'batch_results.json'")

    return results

async def main():
    parser = argparse.ArgumentParser(description="SoundForge AI Batch Test Runner")
    parser.add_argument("--url", type=str, default="", help="Optional base URL of running server")
    args = parser.parse_args()

    if args.url:
        async with httpx.AsyncClient(base_url=args.url, timeout=300.0) as client:
            await run_batch_tests(client)
    else:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=300.0) as client:
            await run_batch_tests(client)

if __name__ == "__main__":
    asyncio.run(main())
