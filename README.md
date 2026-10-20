# SoundForge AI: AI Background Music Engine for Video

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python)](https://www.python.org/)
[![OpenAPI 3.1](https://img.shields.io/badge/OpenAPI-3.1.0-6BA539.svg)](file:///openapi.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Commercial Clearance](https://img.shields.io/badge/Commercial_Clearance-100%25_Verified-brightgreen.svg)](SOURCES.md)
[![Tests](https://img.shields.io/badge/Tests-28%2F28_Passing-brightgreen.svg)]()

**SoundForge AI** is an enterprise-grade AI Background Music Engine built for the **IncuBrix Software Engineer Assessment (Problem Statement PS1)**. It provides automated, high-fidelity background music generation tailored for video creators, editors, podcasts, and automated media pipelines.

---

## Key Highlights & PS1 Compliance

- **Asynchronous Background Job Pipeline**: Submissions return `HTTP 202 Accepted` immediately with a unique `job_id`, real-time stage progress polling (`0.0` to `1.0` and `0` to `100%`), and idempotent execution via `Idempotency-Key` headers.
- **Dual API Contract & Compatibility**: Supports the official IncuBrix contract (`duration_s`, `tempo_bpm`, `loopable`, `output.sample_rate`, `output.target_lufs`, `output.formats`) alongside backward-compatible aliases.
- **Genuine Multi-Track Instrument Stems**: Zero frequency-splitting policy! Stems (Drums, Bass, Chords/Harmony, Melody/Lead) are synthesized independently from generative score logic, eliminating acoustic phase artifacts and bleed.
- **Exact Mathematical Mix Reconstruction**: Master mixes linearly reconstruct from saved disk stems using documented manifest gains ($Mix = \sum g_i \cdot Stem_i$), mathematically verified with error $< 10^{-6}$ (empirically $\le 3.87 \times 10^{-7}$).
- **Loudness & True Peak Mastering**: Automated mastering adhering to **ITU-R BS.1770-4 / EBU R128** loudness targeting (PS1 default `-16.0` LUFS, $\pm 1.0$ LU tolerance) and True Peak limiting strictly maintaining inter-sample headroom ($\le -1.0$ dBTP).
- **Sidechain Narration Ducking**: Envelope-follower sidechain compression automatically attenuates instrumental audio by `-12.0` dB during dialogue passages without pumping, producing a clean `mix_ducked.wav`.
- **HMAC Callback Webhooks**: Asynchronous notifications signed with HMAC-SHA256 in the `X-IncuBrix-Signature` header.
- **Structured Error Schema**: Uniform JSON error responses formatted as `{"error": {"code": "UPPER_SNAKE_CASE", "message": "...", "retryable": false, "details": {}}}`.
- **100% Cleared Commercial Rights**: 100% procedural DSP synthesis. Zero proprietary soundfonts, copyrighted sample packs, or non-commercial model weights.

---

## System Architecture

```
                                  Client Request
                                        |
                            POST /api/v1/music/jobs
                            (with Idempotency-Key)
                                        v
+-----------------------------------------------------------------------------------+
| FastAPI Service Layer                                                             |
|   - Request Validation (Duration: 5-300s, SR: 44.1/48/96kHz, Formats: WAV/MP3)   |
|   - Idempotency Cache (SHA256 Payload Hash Matching & Conflict Detection)         |
|   - Background Async Job Manager (Queue, State Tracking, Webhooks)               |
|   - Correlation ID Middleware (X-Correlation-ID Injection & Log Context)          |
|   - Structured Error Handlers (UPPER_SNAKE_CASE Codes & JSON Schema)              |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
| Provider-Adapter Interface (soundforge/providers/)                                |
|   ├── ProceduralDSPProvider (Default): Real procedural DSP generation             |
|   └── MockDeterministicProvider: Zero-compute fast testing & failure simulation    |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
| Procedural DSP Synthesis Engine                                                   |
|   - Prompt Intent Analyzer & Guardrails (Vocals, Artists, Contradictory Prompts)  |
|   - Harmony Arranger (Chord Progressions, Voicings, Section Grids)               |
|   - 4 Independent Synthesizers:                                                   |
|       * Drums: Sub-sine Kick, Shaped-noise Snare, Resonant Hi-Hats, Crash         |
|       * Bass: Subtractive Saw/Square with Resonant Low-Pass Filter                |
|       * Chords: Polyphonic Supersaw/Warm Pad with Stereo Detune                   |
|       * Melody: Pentatonic/Modal Lead Synthesizer with Expressive Motifs          |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
| Audio Engineering & Mastering Stage                                               |
|   - Linear Stem Summing (Documented Gains: Drums 0.85, Bass 0.80, Chords 0.70,...) |
|   - Mathematical Reconstruction Verification (|Mix - Sum(Gains)| <= 3.87e-07)    |
|   - EBU R128 Loudness Normalizer (pyloudnorm BS.1770-4 target -16.0 LUFS)         |
|   - True Peak Headroom Limiter (Inter-sample peak <= -1.0 dBTP)                   |
|   - Sidechain Narration Ducking (Envelope Follower, -12 dB Attenuation)           |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
| Output Packaging & Manifest                                                       |
|   - 48 kHz 24-bit Stereo WAV Mix, MP3 (if requested), Ducked Mix, 4 Stem WAVs     |
|   - Dual Artifact Links: mix_ducked.wav & ducked_mix.wav, music_manifest.json     |
|   - PS1 JSON Manifest (Settings, Timings, Provenance, Commercial Licenses)        |
+-----------------------------------------------------------------------------------+
```

---

## Quickstart & Installation (Fewer than 10 Commands)

```powershell
# 1. Clone repository
git clone https://github.com/Premkumar2312-pw/soundforge-ai.git
cd soundforge-ai

# 2. Activate virtual environment
venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy configuration template
Copy-Item .env.example .env

# 5. Run full automated test suite (28 passing tests)
python -m pytest tests/ -v

# 6. Run the 10 diverse musical styles batch runner
python scripts/batch_runner.py --suite ten_prompts

# 7. Start the API server
uvicorn soundforge.api.app:app --host 0.0.0.0 --port 8000
```

Once started:
- **Demo UI**: [http://localhost:8000/demo](http://localhost:8000/demo)
- **OpenAPI 3.1 Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Liveness Probe**: [http://localhost:8000/health](http://localhost:8000/health)
- **Readiness Probe**: [http://localhost:8000/ready](http://localhost:8000/ready)

---

## Docker Compose (Reproducible Execution)

```powershell
# Build and start containerized stack
docker compose up --build -d

# Check readiness probe
Invoke-RestMethod http://localhost:8000/ready

# View live structured logs
docker compose logs -f soundforge-api

# Stop containers
docker compose down
```

---

## API Reference & Examples

### 1. Submit Music Generation Job (Asynchronous)
`POST /api/v1/music/jobs`

**Request Body (Assessment Format)**:
```json
{
  "prompt": "Upbeat tech corporate background music with inspiring rhythm",
  "duration_s": 15.0,
  "tempo_bpm": 120.0,
  "key": "G_major",
  "loopable": true,
  "output": {
    "sample_rate": 48000,
    "target_lufs": -16.0,
    "formats": ["wav", "mp3"]
  },
  "sections": [
    {"start_s": 0.0, "mood": "intro"},
    {"start_s": 5.0, "mood": "verse"},
    {"start_s": 10.0, "mood": "chorus"}
  ],
  "seed": 42
}
```

**Headers**:
- `Idempotency-Key`: `demo-key-101` (prevents duplicate generation)
- `X-Correlation-ID`: `corr-trace-001` (distributed tracing)

**Response (`HTTP 202 Accepted`)**:
```json
{
  "job_id": "7b8e3a24-2c09-4a91-9e88-34ebae3d82a1",
  "status": "queued",
  "message": "Background music generation job accepted and enqueued.",
  "created_at": "2026-10-19T18:00:00Z",
  "estimated_duration_seconds": 1.8,
  "idempotency_key": "demo-key-101",
  "correlation_id": "corr-trace-001"
}
```

### 2. Poll Status & Progress
`GET /api/v1/jobs/{job_id}` (or alias `GET /api/v1/music/jobs/{job_id}`)

**Response (`HTTP 200 OK`)**:
```json
{
  "job_id": "7b8e3a24-2c09-4a91-9e88-34ebae3d82a1",
  "status": "succeeded",
  "progress": 1.0,
  "progress_percent": 100,
  "current_stage": "Succeeded",
  "created_at": "2026-10-19T18:00:00Z",
  "completed_at": "2026-10-19T18:00:02Z",
  "artifacts": {
    "mix_wav": "/api/v1/jobs/7b8e3a24-2c09-4a91-9e88-34ebae3d82a1/artifacts/mix.wav",
    "mix_mp3": "/api/v1/jobs/7b8e3a24-2c09-4a91-9e88-34ebae3d82a1/artifacts/mix.mp3",
    "stem_drums": "/api/v1/jobs/7b8e3a24-2c09-4a91-9e88-34ebae3d82a1/artifacts/stem_drums.wav",
    "stem_bass": "/api/v1/jobs/7b8e3a24-2c09-4a91-9e88-34ebae3d82a1/artifacts/stem_bass.wav",
    "stem_chords": "/api/v1/jobs/7b8e3a24-2c09-4a91-9e88-34ebae3d82a1/artifacts/stem_chords.wav",
    "stem_melody": "/api/v1/jobs/7b8e3a24-2c09-4a91-9e88-34ebae3d82a1/artifacts/stem_melody.wav",
    "music_manifest_json": "/api/v1/jobs/7b8e3a24-2c09-4a91-9e88-34ebae3d82a1/artifacts/music_manifest.json"
  },
  "manifest": { ... }
}
```

### 3. Download Artifacts
- `GET /api/v1/jobs/{job_id}/artifacts/mix.wav`
- `GET /api/v1/jobs/{job_id}/artifacts/mix.mp3`
- `GET /api/v1/jobs/{job_id}/artifacts/mix_ducked.wav` (when narration provided)
- `GET /api/v1/jobs/{job_id}/artifacts/stem_drums.wav` (also `stems/drums.wav`)
- `GET /api/v1/jobs/{job_id}/artifacts/music_manifest.json`

---

## Structured Error Codes (Integration Standard #5)

All errors return the exact schema:
```json
{
  "error": {
    "code": "UPPER_SNAKE_CASE",
    "message": "Human-readable description",
    "retryable": false,
    "details": {}
  }
}
```

| HTTP Status | Error Code | Retryable | Cause / Solution |
| :---: | :--- | :---: | :--- |
| `400` | `BAD_REQUEST` | No | Malformed request or state conflict. |
| `404` | `NOT_FOUND` | No | Job ID or artifact filename does not exist. |
| `409` | `IDEMPOTENCY_CONFLICT` | No | Same `Idempotency-Key` was submitted with a different request payload. |
| `422` | `VALIDATION_ERROR` | No | Duration outside 5.0–300.0s, invalid sample rate, or unsupported format. |
| `500` | `INTERNAL_SERVER_ERROR` | Yes | Unhandled internal exception; correlation ID attached. |
| `503` | `SERVICE_UNAVAILABLE` | Yes | Storage backend or service dependency unreachable. |

---

## Automated Batch Runner CLI

SoundForge AI includes an automated batch test runner (`scripts/batch_runner.py`):

```powershell
# Run the 10 Diverse Musical Styles Pack (Assessment 2.C)
python scripts/batch_runner.py --suite ten_prompts

# Run the 10 Hard Cases & Edge Cases Pack (Assessment 3)
python scripts/batch_runner.py --suite hard_cases

# Run all test packs against a live running server
python scripts/batch_runner.py --url http://localhost:8000 --suite all
```

Output reports are saved automatically to `test_output/` in both JSON and CSV formats.

---

## Project Documentation Index

- [OPENAPI.YAML](openapi.yaml) — Authoritative OpenAPI 3.1.0 Specification
- [GUIDE.MD](GUIDE.md) — Comprehensive Windows Operations & Troubleshooting Manual
- [CONFIGURE.MD](CONFIGURE.md) — Complete Environment Variables & Configuration Reference
- [AUDIT_REPORT.MD](AUDIT_REPORT.md) — Requirement-by-Requirement Verification Matrix
- [SUBMISSION_CHECKLIST.MD](SUBMISSION_CHECKLIST.md) — 8-Tab IncuBrix Workbook Data Reference
- [SOURCES.MD](SOURCES.md) — Commercial Clearance, Licensing Audit & Authoritative Links
- [AI_USE.MD](AI_USE.md) — AI Assistance Disclosure & Development Traceability
- [REPORT.MD](REPORT.md) — Engineering Architecture, Design Decisions & Benchmarks
