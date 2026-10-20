import os
import sys
sys.path.insert(0, os.path.abspath("."))
import time
import soundfile as sf
from fastapi.testclient import TestClient
from soundforge.api.app import app

def test_full_ui_and_api_workflow():
    client = TestClient(app)
    print("=== TESTING COMPLETE DEMO UI & GENERATION WORKFLOW ===")

    # 1. Test GET /demo
    resp_demo = client.get("/demo")
    assert resp_demo.status_code == 200
    html = resp_demo.text
    print(f"[PASS] GET /demo returned HTTP 200 ({len(html)} bytes)")

    # 2. Verify all UI components and IDs expected by the browser
    expected_ids = [
        "promptInput", "durationSlider", "durationVal",
        "sectionEditorBox", "tempoSlider", "tempoVal",
        "keySelect", "lufsSlider", "lufsVal",
        "loopCheck", "mp3Check", "narrationUrlInput",
        "narrationFileInput", "seedInput", "sampleRateSelect",
        "generateBtn", "progressMonitor", "progressFill",
        "progressStage", "progressPct", "progressElapsed",
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
    for eid in expected_ids:
        assert f'id="{eid}"' in html, f"Missing expected ID '{eid}' in demo HTML"
    print(f"[PASS] All {len(expected_ids)} interactive UI elements verified in HTML")

    # 3. Verify JavaScript status handler supports 'succeeded' and State Machine
    assert "data.status === 'succeeded'" in html, "JavaScript must check for 'succeeded' status"
    assert "resolveArtifactUrl" in html, "JavaScript must have resolveArtifactUrl helper"
    assert "AppState" in html, "JavaScript must have AppState state machine"
    print("[PASS] JavaScript status condition, state machine, and URL resolution verified")

    # 4. Simulate the exact form submission from submitMusicJob()
    form_payload = {
        "prompt": "Upbeat modern corporate tech tutorial with bright rhythm",
        "duration_s": 5.0,
        "duration": 5.0,
        "tempo_bpm": 120.0,
        "tempo": 120.0,
        "key": "C_major",
        "loopable": False,
        "loopability": False,
        "target_loudness": -16.0,
        "output_formats": ["wav", "mp3"]
    }
    submit_resp = client.post("/api/v1/music/jobs", json=form_payload)
    assert submit_resp.status_code == 202
    job_data = submit_resp.json()
    job_id = job_data["job_id"]
    print(f"[PASS] Job submitted via POST /api/v1/music/jobs -> HTTP 202, job_id={job_id}")

    # 5. Simulate pollJob(job_id)
    max_retries = 40
    completed = False
    final_data = None
    for _ in range(max_retries):
        time.sleep(0.4)
        poll_resp = client.get(f"/api/v1/music/jobs/{job_id}")
        assert poll_resp.status_code == 200
        final_data = poll_resp.json()
        status = final_data.get("status")
        progress = final_data.get("progress", 0.0)
        stage = final_data.get("current_stage", "")
        # print(f"  Polling: {status} ({progress*100:.0f}%) - {stage}")
        if status in ("succeeded", "completed"):
            completed = True
            break
        elif status == "failed":
            raise RuntimeError(f"Job failed unexpectedly: {final_data.get('error')}")

    assert completed is True, f"Job did not complete within timeout. Last status: {final_data.get('status')}"
    print(f"[PASS] Polling reached '{final_data['status']}' with progress={final_data['progress']}")

    # 6. Verify Artifacts returned to UI
    artifacts = final_data.get("artifacts")
    assert artifacts is not None, "artifacts dictionary missing from response"
    print(f"[PASS] Artifacts received: {list(artifacts.keys())}")

    # 7. Test each artifact URL resolution and download (same as browser)
    for art_key, rel_url in artifacts.items():
        # Ensure URL starts with /api/v1/
        assert rel_url.startswith("/api/v1/"), f"Unexpected artifact URL path: {rel_url}"
        download_resp = client.get(rel_url)
        assert download_resp.status_code == 200, f"Failed to download {art_key} from {rel_url}: HTTP {download_resp.status_code}"
        content_len = len(download_resp.content)
        assert content_len > 100, f"Artifact {art_key} returned empty body ({content_len} bytes)"

        # If audio, verify it can be parsed by soundfile
        if art_key.endswith(("_wav", "_mp3")):
            import io
            audio_data, sr = sf.read(io.BytesIO(download_resp.content))
            dur = len(audio_data) / sr
            assert sr == 48000
            assert abs(dur - 5.0) <= 0.05
            print(f"  [PASS] Downloaded {art_key}: {content_len} bytes, sr={sr}, dur={dur:.2f}s")
        elif art_key.endswith("_json"):
            import json
            mf_data = json.loads(download_resp.content.decode("utf-8"))
            assert mf_data.get("status") == "succeeded"
            print(f"  [PASS] Downloaded {art_key}: {content_len} bytes, status={mf_data.get('status')}")

    print("\n=== ALL DEMO UI & GENERATION WORKFLOW TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_full_ui_and_api_workflow()
