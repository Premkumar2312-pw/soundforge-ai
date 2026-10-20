import time
import httpx

base = "http://localhost:8000"

print("Waiting for container health...")
for i in range(25):
    try:
        r = httpx.get(f"{base}/health", timeout=3.0)
        if r.status_code == 200:
            print(f"[PASS] /health responded: {r.json()}")
            break
    except Exception as e:
        time.sleep(1.0)
else:
    raise RuntimeError("Timed out waiting for container /health")

# Check readiness probe
r_ready = httpx.get(f"{base}/ready", timeout=3.0)
assert r_ready.status_code == 200, f"/ready returned {r_ready.status_code}"
print(f"[PASS] /ready responded: {r_ready.json()}")

# Check demo page
r_demo = httpx.get(f"{base}/demo", timeout=3.0)
assert r_demo.status_code == 200, f"/demo returned {r_demo.status_code}"
assert "SoundForge AI" in r_demo.text
assert "AppState" in r_demo.text
print(f"[PASS] /demo returned 200 OK ({len(r_demo.text)} bytes)")

# Test job submission on container
payload = {
    "prompt": "Containerized integration test: Uplifting acoustic folk with gentle rhythm",
    "duration_s": 5.0,
    "tempo_bpm": 110.0,
    "output_formats": ["wav", "mp3"]
}
sub = httpx.post(f"{base}/api/v1/music/jobs", json=payload, timeout=5.0)
assert sub.status_code == 202, f"POST /api/v1/music/jobs returned {sub.status_code}"
job_id = sub.json()["job_id"]
print(f"[PASS] Submitted container job: {job_id}")

# Poll status
done = False
for _ in range(30):
    time.sleep(0.5)
    poll = httpx.get(f"{base}/api/v1/music/jobs/{job_id}", timeout=3.0).json()
    if poll.get("status") in ("succeeded", "completed"):
        done = True
        break
    elif poll.get("status") == "failed":
        raise RuntimeError(f"Job failed on container: {poll.get('error')}")

assert done is True
print(f"[PASS] Container job reached status: {poll.get('status')}")
artifacts = poll.get("artifacts", {})
print(f"[PASS] Artifacts generated: {list(artifacts.keys())}")

# Download mix.wav and mix.mp3
wav_resp = httpx.get(f"{base}{artifacts['mix_wav']}", timeout=5.0)
assert wav_resp.status_code == 200
assert len(wav_resp.content) > 1000000
print(f"[PASS] Downloaded mix.wav ({len(wav_resp.content)} bytes) from container")

mp3_resp = httpx.get(f"{base}{artifacts['mix_mp3']}", timeout=5.0)
assert mp3_resp.status_code == 200
assert len(mp3_resp.content) > 50000
print(f"[PASS] Downloaded mix.mp3 ({len(mp3_resp.content)} bytes) from container")

print("\n=== CONTAINERIZED API & DEMO FULLY VERIFIED ===")
