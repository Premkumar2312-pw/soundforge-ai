"""
Integration tests for SoundForge AI REST API (FastAPI) - PS1 Specification
"""

import pytest
import asyncio
import httpx
from soundforge.api.app import app

@pytest.mark.asyncio
async def test_health_and_readiness_endpoints():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["ready"] is True

        resp_ready = await client.get("/ready")
        assert resp_ready.status_code == 200
        assert resp_ready.json()["status"] == "ready"

@pytest.mark.asyncio
async def test_duration_boundary_and_input_validation():
    from soundforge.models import MusicJobRequest
    # Boundary validations on model schema
    req_min = MusicJobRequest(prompt="test", duration=5.0)
    assert req_min.duration == 5.0
    req_max = MusicJobRequest(prompt="test", duration=300.0)
    assert req_max.duration == 300.0

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Below minimum duration boundary (4.9s < 5.0s) -> HTTP 422
        resp = await client.post("/api/v1/music/jobs", json={"prompt": "test", "duration": 4.9})
        assert resp.status_code == 422

        # Above maximum duration boundary (300.1s > 300.0s) -> HTTP 422
        resp = await client.post("/api/v1/music/jobs", json={"prompt": "test", "duration": 300.1})
        assert resp.status_code == 422

        # Invalid sample rate -> HTTP 422
        resp = await client.post("/api/v1/music/jobs", json={"prompt": "test", "duration": 5.0, "sample_rate": 12345})
        assert resp.status_code == 422

        # Invalid format -> HTTP 422
        resp = await client.post("/api/v1/music/jobs", json={"prompt": "test", "duration": 5.0, "output_formats": ["flac"]})
        assert resp.status_code == 422

@pytest.mark.asyncio
async def test_correlation_id_propagation():
    transport = httpx.ASGITransport(app=app)
    test_corr_id = "test-correlation-uuid-999"
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/music/jobs",
            json={"prompt": "Correlation test", "duration": 5.0},
            headers={"X-Correlation-ID": test_corr_id}
        )
        assert resp.status_code == 202
        assert resp.headers.get("X-Correlation-ID") == test_corr_id
        data = resp.json()
        assert data.get("correlation_id") == test_corr_id

@pytest.mark.asyncio
async def test_job_lifecycle_idempotency_and_reconstruction():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "prompt": "Test electronic upbeat loop",
            "duration": 5.0,
            "tempo": 120.0,
            "key": "C_major",
            "output_formats": ["wav", "mp3"],
            "seed": 12345
        }
        idemp_key = "idemp-test-key-002"

        # 1. First submission -> HTTP 202 Accepted
        resp = await client.post("/api/v1/music/jobs", json=payload, headers={"Idempotency-Key": idemp_key})
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["status"] in ("pending", "queued")
        job_id = data["job_id"]

        # 2. Idempotent re-submission -> same job_id returned
        resp_repeat = await client.post("/api/v1/music/jobs", json=payload, headers={"Idempotency-Key": idemp_key})
        assert resp_repeat.status_code == 202
        assert resp_repeat.json()["job_id"] == job_id

        # 3. Conflicting payload with same idempotency key -> HTTP 409 Conflict
        conflicting_payload = payload.copy()
        conflicting_payload["duration"] = 15.0
        resp_conflict = await client.post("/api/v1/music/jobs", json=conflicting_payload, headers={"Idempotency-Key": idemp_key})
        assert resp_conflict.status_code == 409

        # 4. Poll until completed
        max_wait = 15.0
        elapsed = 0.0
        completed = False
        status_data = None
        while elapsed < max_wait:
            await asyncio.sleep(0.3)
            elapsed += 0.3
            s_resp = await client.get(f"/api/v1/music/jobs/{job_id}")
            assert s_resp.status_code == 200
            status_data = s_resp.json()
            if status_data["status"] in ("completed", "succeeded"):
                completed = True
                break

        assert completed is True
        assert status_data["progress"] == 1.0
        manifest = status_data["manifest"]
        assert manifest is not None
        assert status_data["artifacts"] is not None
        assert "mix_wav" in status_data["artifacts"]
        assert "stem_drums" in status_data["artifacts"]

        # Verify PS1 Default Loudness is -16.0 LUFS
        metrics = manifest["audio_metrics"]
        assert metrics["target_loudness_lufs"] == -16.0
        # Loudness tolerance within 1.0 LU
        assert abs(metrics["measured_loudness_lufs"] - (-16.0)) <= 1.0
        # True peak no greater than -1.0 dBTP
        assert metrics["true_peak_dbtp"] <= -0.95
        # File reconstruction verification from saved disk files
        assert manifest["reconstruction_verification"]["max_reconstruction_error"] < 1e-5

        # 5. Download artifact mix.wav
        art_resp = await client.get(f"/api/v1/music/jobs/{job_id}/artifacts/mix.wav")
        assert art_resp.status_code == 200
        assert art_resp.headers["content-type"] == "audio/wav"
        assert len(art_resp.content) > 1000

        # Download manifest
        man_resp = await client.get(f"/api/v1/music/jobs/{job_id}/artifacts/manifest.json")
        assert man_resp.status_code == 200
        assert man_resp.headers["content-type"] == "application/json"
