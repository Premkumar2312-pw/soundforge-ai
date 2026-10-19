"""
Tests for IncuBrix Assessment Contract, Structured Errors, Webhooks, and Hard Cases
"""

import pytest
import hmac
import hashlib
import json
import numpy as np
import httpx

from soundforge.api.app import app
from soundforge.models import MusicJobRequest, JobStatus
from soundforge.config import settings
from soundforge.providers.mock import MockDeterministicProvider
from soundforge.providers.procedural import ProceduralDSPProvider
from soundforge.dsp.synthesis import ProceduralSynthesizer, compute_stem_bleed_matrix
from soundforge.dsp.music_theory import analyze_prompt_musicality, calculate_sections
from soundforge.dsp.ducking import is_ssrf_safe_url

@pytest.mark.asyncio
async def test_incubrix_request_contract_and_alias_routes():
    """Verify POST /api/v1/music/jobs with duration_s, tempo_bpm, loopable, output, and GET /api/v1/jobs/{job_id}."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "prompt": "IncuBrix contract compliance test",
            "duration_s": 5.0,
            "tempo_bpm": 124.0,
            "loopable": True,
            "output": {
                "sample_rate": 48000,
                "target_lufs": -16.0,
                "formats": ["wav", "mp3"]
            },
            "sections": [
                {"start_s": 0.0, "mood": "intro"},
                {"start_s": 2.5, "mood": "main"}
            ]
        }
        resp = await client.post("/api/v1/music/jobs", json=payload)
        assert resp.status_code == 202
        data = resp.json()
        assert "job_id" in data
        assert data["status"] in (JobStatus.QUEUED.value, "queued", "pending")
        job_id = data["job_id"]

        # Verify status endpoint at /api/v1/jobs/{job_id} (Assessment contract)
        status_resp = await client.get(f"/api/v1/jobs/{job_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["job_id"] == job_id
        assert "progress" in status_data
        assert "progress_percent" in status_data

@pytest.mark.asyncio
async def test_structured_error_responses():
    """Verify structured error format: {"error": {"code": "...", "message": "...", "retryable": ..., "details": ...}}."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. 422 Validation Error (duration below 5.0s)
        resp_422 = await client.post("/api/v1/music/jobs", json={"prompt": "Short", "duration_s": 2.0})
        assert resp_422.status_code == 422
        body_422 = resp_422.json()
        assert "error" in body_422
        assert body_422["error"]["code"] == "VALIDATION_ERROR"
        assert body_422["error"]["retryable"] is False
        assert "validation_errors" in body_422["error"]["details"]

        # 2. 404 Not Found
        resp_404 = await client.get("/api/v1/jobs/nonexistent-uuid-000")
        assert resp_404.status_code == 404
        body_404 = resp_404.json()
        assert "error" in body_404
        assert body_404["error"]["code"] == "NOT_FOUND"

        # 3. 409 Idempotency Conflict
        idemp_key = "test-conflict-idemp-001"
        p1 = {"prompt": "First prompt", "duration_s": 5.0}
        p2 = {"prompt": "Second differing prompt", "duration_s": 6.0}
        await client.post("/api/v1/music/jobs", json=p1, headers={"Idempotency-Key": idemp_key})
        resp_409 = await client.post("/api/v1/music/jobs", json=p2, headers={"Idempotency-Key": idemp_key})
        assert resp_409.status_code == 409
        body_409 = resp_409.json()
        assert "error" in body_409
        assert body_409["error"]["code"] == "IDEMPOTENCY_CONFLICT"

def test_vocal_and_artist_guardrails():
    """Verify vocal requests and copyrighted artist names generate warnings and remain instrumental."""
    # Vocal prompt
    vocal_analysis = analyze_prompt_musicality("A song with uplifting female vocals and lyrics")
    assert any("Vocals/singing" in w for w in vocal_analysis["warnings"])
    assert vocal_analysis["energy"] in ["high", "medium"]

    # Artist prompt
    artist_analysis = analyze_prompt_musicality("Orchestral soundtrack like Hans Zimmer")
    assert any("hans zimmer" in w for w in artist_analysis["warnings"])

    # Contradictory prompt
    contra_analysis = analyze_prompt_musicality("Calm but aggressive techno beats")
    assert any("Contradictory" in w for w in contra_analysis["warnings"])

def test_single_stem_regeneration_and_bleed():
    """Verify single stem can be regenerated while other stems remain byte-for-byte reproducible."""
    synth1 = ProceduralSynthesizer(sample_rate=48000, seed=123)
    synth2 = ProceduralSynthesizer(sample_rate=48000, seed=123)

    sections = calculate_sections(5.0, None, bpm=120.0)
    chords = [{"root": 36, "root_name": "C", "notes": [60, 64, 67, 71]}]

    all_stems = synth1.render_all_stems(5.0, 120.0, sections, chords)
    single_bass = synth2.render_single_stem("bass", 5.0, 120.0, sections, chords)

    # Generated single bass matches the original bass exactly
    np.testing.assert_array_equal(all_stems["bass"], single_bass)

    # Verify stem bleed matrix demonstrates independent instrument content (cross-correlation < 0.25)
    bleed = compute_stem_bleed_matrix(all_stems)
    assert bleed["independent_stems_verified"] is True
    assert bleed["max_cross_correlation"] < 0.25

def test_ssrf_safety_validation():
    """Verify private/internal network URLs are blocked to prevent SSRF attacks."""
    assert is_ssrf_safe_url("http://127.0.0.1/audio.wav")[0] is False
    assert is_ssrf_safe_url("http://localhost:8000/audio.wav")[0] is False
    assert is_ssrf_safe_url("http://192.168.1.50/audio.wav")[0] is False
    assert is_ssrf_safe_url("http://10.0.0.1/audio.wav")[0] is False
    assert is_ssrf_safe_url("ftp://example.com/audio.wav")[0] is False
    assert is_ssrf_safe_url("https://example.com/audio.wav")[0] is True

@pytest.mark.asyncio
async def test_mock_deterministic_provider_and_failure_simulation(tmp_path):
    """Verify MockDeterministicProvider runs in zero compute and handles simulated failures."""
    mock_prov = MockDeterministicProvider()
    req = MusicJobRequest(prompt="Mock test", duration_s=5.0)

    # 1. Normal fast generation
    manifest = await mock_prov.generate("test-mock-job", req, str(tmp_path))
    assert manifest["status"] == "succeeded"
    assert (tmp_path / "mix.wav").exists()
    assert (tmp_path / "music_manifest.json").exists()

    # 2. Hard case #15: Simulated provider failure
    fail_req = MusicJobRequest(prompt="Simulate error __SIMULATE_FAILURE__", duration_s=5.0)
    with pytest.raises(RuntimeError, match="Simulated provider failure"):
        await mock_prov.generate("test-fail-job", fail_req, str(tmp_path))
