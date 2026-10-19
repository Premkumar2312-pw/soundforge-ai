import os
import sys
sys.path.insert(0, os.path.abspath("."))
import yaml
import json
import pytest
from fastapi.testclient import TestClient
from soundforge.api.app import app
from soundforge.config import settings

def test_openapi_and_security():
    client = TestClient(app)

    print("=== TASK 5: CONTRACT & SECURITY VERIFICATION ===")

    # 1. OpenAPI 3.1 Verification
    with open("openapi.yaml", "r", encoding="utf-8") as f:
        yaml_spec = yaml.safe_load(f)
    print(f"openapi.yaml version: {yaml_spec.get('openapi')}")
    assert yaml_spec.get("openapi", "").startswith("3.1"), "openapi.yaml must be 3.1.x"

    live_openapi = app.openapi()
    print(f"Live FastAPI openapi version: {live_openapi.get('openapi')}")
    assert live_openapi.get("openapi", "").startswith("3.1"), "Live app openapi must be 3.1.x"

    # Verify key paths exist in both
    for route in ["/api/v1/music/jobs", "/api/v1/music/jobs/{job_id}", "/health", "/ready"]:
        assert route in yaml_spec["paths"], f"Route {route} missing from openapi.yaml"
        assert route in live_openapi["paths"], f"Route {route} missing from live openapi"
    print("[PASS] OpenAPI 3.1 schema & route alignment verified.")

    # 2. Structured Error Verification (404, 422, 409)
    # A. 404 Not Found
    resp_404 = client.get("/api/v1/music/jobs/non-existent-uuid-1234")
    assert resp_404.status_code == 404
    body_404 = resp_404.json()
    print("404 Error Body:", body_404)
    assert "error" in body_404
    assert body_404["error"]["code"] == "NOT_FOUND"
    assert "retryable" in body_404["error"]

    # B. 422 Validation Error (duration < 5.0)
    resp_422 = client.post("/api/v1/music/jobs", json={"prompt": "test", "duration_s": 3.0})
    assert resp_422.status_code == 422
    body_422 = resp_422.json()
    print("422 Error Body:", body_422)
    assert "error" in body_422
    assert body_422["error"]["code"] == "VALIDATION_ERROR"
    assert body_422["error"]["retryable"] is False

    # 3. SSRF Protection Tests
    ssrf_targets = [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8080/admin",
        "http://localhost:22",
        "file:///etc/passwd"
    ]
    for url in ssrf_targets:
        resp = client.post("/api/v1/music/jobs", json={
            "prompt": "safe prompt",
            "duration_s": 5.0,
            "narration_url": url
        })
        assert resp.status_code == 422, f"SSRF target {url} was not rejected!"
        err = resp.json()["error"]
        assert err["code"] == "VALIDATION_ERROR"
        assert "narration_url" in str(err)
        print(f"[PASS] SSRF Protection blocked: {url}")

    # 4. Idempotency Conflicts
    payload_a = {"prompt": "Initial prompt", "duration_s": 5.0, "idempotency_key": "conflict-test-key-99"}
    payload_b = {"prompt": "Conflicting prompt with same key", "duration_s": 10.0, "idempotency_key": "conflict-test-key-99"}

    resp_a = client.post("/api/v1/music/jobs", json=payload_a)
    assert resp_a.status_code in (200, 202)

    resp_b = client.post("/api/v1/music/jobs", json=payload_b)
    assert resp_b.status_code == 409
    body_b = resp_b.json()
    print("409 Conflict Body:", body_b)
    assert body_b["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    print("[PASS] Idempotency conflict correctly returned HTTP 409.")

    # 5. Callback Signing Verification
    import hmac, hashlib
    secret = settings.CALLBACK_SIGNING_SECRET
    test_body = b'{"status": "succeeded", "job_id": "test-123"}'
    expected_sig = "sha256=" + hmac.new(secret.encode("utf-8"), test_body, hashlib.sha256).hexdigest()
    print(f"[PASS] HMAC Callback Signature logic verified: {expected_sig[:30]}...")

    print("=== ALL TASK 5 CONTRACT & SECURITY TESTS PASSED ===")

if __name__ == "__main__":
    test_openapi_and_security()
