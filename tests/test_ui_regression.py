"""
UI Regression & State Isolation Tests for SoundForge AI
Verifies state machine transitions, previous result isolation, and narration upload.
"""

import os
import io
import time
import pytest
import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient
from soundforge.api.app import app
from soundforge.api.ui import DEMO_HTML

client = TestClient(app)

def test_ui_dom_elements_and_state_machine():
    """Verify Demo UI contains all required creator tool controls and state machine logic."""
    resp = client.get("/demo")
    assert resp.status_code == 200
    html = resp.text

    # Form groups & controls
    required_ids = [
        "promptInput", "durationSlider", "durationVal",
        "sectionEditorBox", "tempoSlider", "tempoVal",
        "keySelect", "lufsSlider", "lufsVal",
        "loopCheck", "mp3Check", "narrationUrlInput",
        "narrationFileInput", "seedInput", "sampleRateSelect",
        "generateBtn", "progressMonitor", "progressFill",
        "progressStage", "progressPct", "progressElapsed"
    ]
    for rid in required_ids:
        assert f'id="{rid}"' in html, f"Missing form control: {rid}"

    # Results & Stems Multi-Track mixer
    result_ids = [
        "emptyPlaceholder", "activeResultsContainer", "errorCard",
        "errorTitle", "errorMessage", "retryActionRow",
        "activeJobIdText", "activeStatusPill",
        "metricDuration", "metricSampleRate", "metricLoudness", "metricPeak", "metricRecon",
        "audioMasterMix", "masterDownloadsGroup",
        "btnSyncPlayAll", "channelDrums", "channelBass", "channelChords", "channelMelody",
        "audioStemDrums", "audioStemBass", "audioStemChords", "audioStemMelody",
        "soloDrums", "soloBass", "soloChords", "soloMelody",
        "muteDrums", "muteBass", "muteChords", "muteMelody",
        "dlStemDrums", "dlStemBass", "dlStemChords", "dlStemMelody",
        "manifestCodeViewer", "dlManifestBtn",
        "previousResultCard", "prevJobPill", "audioPrevMix", "prevDownloadLinks"
    ]
    for rid in result_ids:
        assert f'id="{rid}"' in html, f"Missing result element: {rid}"

    # State Machine checks in JS
    assert "AppState" in html
    assert "IDLE" in html and "SUBMITTING" in html and "RUNNING" in html
    assert "SUCCEEDED" in html and "FAILED" in html and "TIMED_OUT" in html
    assert "archiveCurrentToPrevious" in html
    assert "seqId !== session.seq" in html  # Stale response protection
    assert "toggleStemSolo" in html
    assert "toggleStemMute" in html
    assert "setStemVolume" in html
    assert "togglePlayAllStems" in html

def test_narration_upload_and_ducking_workflow(tmp_path):
    """Verify narration upload endpoint saves audio and enables sidechain ducking."""
    # 1. Create a dummy narration WAV
    sr = 48000
    duration = 4.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    voice = (0.5 * np.sin(2.0 * np.pi * 300.0 * t)).astype(np.float32)
    stereo_voice = np.column_stack((voice, voice))

    buf = io.BytesIO()
    sf.write(buf, stereo_voice, sr, format='WAV', subtype='PCM_16')
    buf.seek(0)

    # 2. Upload narration via POST /api/v1/narration/upload
    upload_resp = client.post(
        "/api/v1/narration/upload",
        files={"file": ("test_narration.wav", buf, "audio/wav")}
    )
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    assert upload_data["status"] == "uploaded"
    assert "narration_url" in upload_data
    assert upload_data["duration_s"] == 4.0
    assert upload_data["sample_rate"] == 48000
    narration_url = upload_data["narration_url"]

    # 3. Stream back uploaded narration
    file_resp = client.get(narration_url)
    assert file_resp.status_code == 200
    assert file_resp.headers["content-type"] == "audio/wav"

    # 4. Create music job with the uploaded narration URL
    job_resp = client.post("/api/v1/music/jobs", json={
        "prompt": "Corporate tutorial with narration voiceover",
        "duration_s": 6.0,
        "narration_url": narration_url,
        "output_formats": ["wav", "mp3"]
    })
    assert job_resp.status_code == 202
    job_id = job_resp.json()["job_id"]

    # Poll until finished
    for _ in range(40):
        time.sleep(0.3)
        poll = client.get(f"/api/v1/music/jobs/{job_id}").json()
        if poll.get("status") in ("succeeded", "completed"):
            break

    assert poll.get("status") == "succeeded"
    artifacts = poll.get("artifacts", {})
    manifest = poll.get("manifest", {})

    # Ducked mix was generated and exposed
    assert "mix_ducked_wav" in artifacts or "ducked_mix_wav" in artifacts
    assert manifest.get("ducking", {}).get("ducking_applied") is True

    ducked_key = "mix_ducked_wav" if "mix_ducked_wav" in artifacts else "ducked_mix_wav"
    ducked_dl = client.get(artifacts[ducked_key])
    assert ducked_dl.status_code == 200
    assert len(ducked_dl.content) > 1000

def test_stale_success_isolation_lifecycle():
    """Verify that a successful job is isolated and not displayed as the status of a subsequent failed attempt."""
    # Job 1: Successful generation
    resp1 = client.post("/api/v1/music/jobs", json={
        "prompt": "First successful job",
        "duration_s": 5.0
    })
    assert resp1.status_code == 202
    job1_id = resp1.json()["job_id"]

    for _ in range(30):
        time.sleep(0.3)
        st1 = client.get(f"/api/v1/music/jobs/{job1_id}").json()
        if st1.get("status") == "succeeded":
            break
    assert st1.get("status") == "succeeded"

    # Job 2: Fails immediately on validation (duration < 5.0s)
    resp2 = client.post("/api/v1/music/jobs", json={
        "prompt": "Second failing job",
        "duration_s": 3.0
    })
    assert resp2.status_code == 422
    err_body = resp2.json()
    assert err_body["error"]["code"] == "VALIDATION_ERROR"
    assert err_body["error"]["retryable"] is False

    # Check that error response conforms to IncuBrix structured error standard
    assert "details" in err_body["error"]
    assert "message" in err_body["error"]
