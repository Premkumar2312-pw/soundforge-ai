"""
SoundForge AI - Automated Batch Test Runner
Executes comprehensive test matrices across diverse musical styles, durations, and edge cases.
"""

import sys
import os
import time
import json
import asyncio
import argparse
import httpx
from typing import List, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from soundforge.api.app import app

TEST_CASES = [
    {
        "id": "TC-01",
        "description": "Standard Corporate Tech Tutorial",
        "payload": {
            "prompt": "Upbeat tech tutorial background music with clean drums and motivating melody",
            "duration": 6.0,
            "tempo": 120.0,
            "key": "C_major",
            "loopability": False,
            "target_loudness": -14.0,
            "output_formats": ["wav", "mp3"],
            "seed": 1001
        }
    },
    {
        "id": "TC-02",
        "description": "Lo-Fi Study Beat (Seamless Loop)",
        "payload": {
            "prompt": "Relaxing lo-fi chill study beat with soft keys and gentle bass",
            "duration": 8.0,
            "tempo": 80.0,
            "key": "A_minor",
            "loopability": True,
            "target_loudness": -14.0,
            "output_formats": ["wav"],
            "seed": 2002
        }
    },
    {
        "id": "TC-03",
        "description": "Cinematic Build-Up with Custom Sections",
        "payload": {
            "prompt": "Epic dramatic trailer intro building up to intense climax",
            "duration": 10.0,
            "tempo": 96.0,
            "key": "D_minor",
            "sections": [
                {"name": "intro", "duration": 2.5},
                {"name": "build", "duration": 4.5},
                {"name": "climax", "duration": 3.0}
            ],
            "loopability": False,
            "target_loudness": -14.0,
            "output_formats": ["wav", "mp3"],
            "seed": 3003
        }
    },
    {
        "id": "TC-04",
        "description": "Synthwave Retro Groove with Broadcast Loudness",
        "payload": {
            "prompt": "80s retro synthwave cyberpunk driving groove",
            "duration": 5.0,
            "tempo": 124.0,
            "key": "F_major",
            "loopability": False,
            "target_loudness": -16.0,
            "output_formats": ["wav"],
            "seed": 4004
        }
    },
    {
        "id": "TC-05",
        "description": "Short Sting / Ident (3.0 seconds)",
        "payload": {
            "prompt": "Modern logo intro sound logo sting",
            "duration": 3.0,
            "loopability": False,
            "target_loudness": -14.0,
            "output_formats": ["wav", "mp3"],
            "seed": 5005
        }
    }
]

async def run_batch_tests(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    print("\n" + "="*80)
    print(" SOUNDFORGE AI - BATCH TEST EXECUTION MATRIX")
    print("="*80 + "\n")

    results = []

    for tc in TEST_CASES:
        tc_id = tc["id"]
        desc = tc["description"]
        payload = tc["payload"]
        print(f"[{tc_id}] Running: {desc} (Duration: {payload['duration']}s)...")

        t_start = time.perf_counter()

        # 1. Submit Job
        headers = {"Idempotency-Key": f"test-idemp-{tc_id}"}
        resp = await client.post("/api/v1/music/jobs", json=payload, headers=headers)

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

        # Test Idempotency with exact same key
        idemp_resp = await client.post("/api/v1/music/jobs", json=payload, headers=headers)
        assert idemp_resp.status_code == 202, f"Idempotency retry failed: {idemp_resp.status_code}"
        assert idemp_resp.json()["job_id"] == job_id, "Idempotency did not return same job_id"

        # 2. Poll Job
        max_wait = 30.0
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

        # Validate specifications
        dur_err = abs(metrics["actual_duration_seconds"] - payload["duration"])
        lufs_err = abs(metrics["measured_loudness_lufs"] - payload["target_loudness"])
        peak_ok = metrics["true_peak_dbtp"] <= metrics["max_true_peak_limit_dbtp"] + 0.1
        recon_ok = recon["max_reconstruction_error"] < 1e-5

        passed = (dur_err < 0.01) and (lufs_err < 1.0) and peak_ok and recon_ok

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
        print(f"  {status_tag} Completed in {total_time}s | LUFS: {metrics['measured_loudness_lufs']} | Peak: {metrics['true_peak_dbtp']} dBTP | Recon Error: {recon['max_reconstruction_error']}")

    print("\n" + "="*80)
    print(" BATCH RUN SUMMARY TABLE")
    print("="*80)
    print(f"{'ID':<7} | {'Status':<6} | {'Target Dur':<10} | {'Act Dur':<8} | {'Target LUFS':<11} | {'Act LUFS':<9} | {'Peak dBTP':<9} | {'Recon Err':<10} | {'Time(s)':<7}")
    print("-" * 92)
    for r in results:
        if r.get("status") == "PASS":
            print(f"{r['id']:<7} | {r['status']:<6} | {r['target_duration_s']:<10.1f} | {r['actual_duration_s']:<8.2f} | {r['target_lufs']:<11.1f} | {r['measured_lufs']:<9.2f} | {r['true_peak_dbtp']:<9.2f} | {r['max_recon_error']:<10.6f} | {r['execution_time_s']:<7.2f}")
        else:
            print(f"{r['id']:<7} | {r['status']:<6} | {r.get('error', 'Unknown failure')}")
    print("="*80 + "\n")

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
        async with httpx.AsyncClient(base_url=args.url, timeout=30.0) as client:
            await run_batch_tests(client)
    else:
        # In-process ASGI execution
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as client:
            await run_batch_tests(client)

if __name__ == "__main__":
    asyncio.run(main())
