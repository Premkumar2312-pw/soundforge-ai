# SoundForge AI: AI Background Music Engine for Video

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Commercial Clearance](https://img.shields.io/badge/Commercial_Clearance-100%25_Verified-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/Tests-10%2F10_Passing-brightgreen.svg)]()

**SoundForge AI** is an enterprise-grade AI Background Music Engine built for the **IncuBrix Software Engineer Assessment (Problem Statement PS1)**. It provides automated, high-fidelity background music generation tailored for video creators, editors, podcasts, and automated media pipelines.

---

## Key Highlights & PS1 Compliance

- **Asynchronous Background Job Pipeline**: Submissions return `HTTP 202 Accepted` immediately with a unique `job_id`, real-time stage progress polling (`0.0` to `1.0`), and idempotent execution via `Idempotency-Key` headers.
- **Genuine Multi-Track Instrument Stems**: Zero frequency-splitting policy! Stems (Drums, Bass, Chords/Harmony, Melody/Lead) are synthesized independently from generative score logic, eliminating acoustic phase artifacts and bleed.
- **Exact Mathematical Mix Reconstruction**: Master mixes linearly reconstruct from stems using documented gains ($Mix = \sum g_i \cdot Stem_i$), mathematically verified with zero error ($0.0$).
- **Loudness & True Peak Mastering**: Automated mastering adhering to **ITU-R BS.1770-4 / EBU R128** loudness targeting (default `-14.0` LUFS) and soft-knee True Peak limiting strictly maintaining inter-sample headroom ($\le -1.0$ dBTP).
- **Sidechain Narration Ducking**: Envelope-follower sidechain compression automatically attenuates instrumental audio by `-12.0` dB during dialogue passages without pumping.
- **Comprehensive PS1 Manifest**: Accompanies every job with complete musical settings, structural sections, beat/bar grids, stem gains, true peak/LUFS metrics, compute cost estimates, execution timings, and licensing provenance.
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
|   - Request Validation (Duration, Sample Rate, Formats, Sections)                  |
|   - Idempotency Cache (SHA256 Payload Hash Matching & Conflict Detection)         |
|   - Background Async Job Manager (Queue, State Tracking, Webhooks)               |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
| Procedural DSP Synthesis Engine                                                   |
|   - Prompt Intent Analyzer (Genre, BPM, Key, Energy Detection)                    |
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
|   - Mathematical Reconstruction Verification (|Mix - Sum(Gains)| == 0.0)         |
|   - EBU R128 Loudness Normalizer (pyloudnorm BS.1770-4)                           |
|   - True Peak Brickwall Limiter (Inter-sample peak <= -1.0 dBTP)                  |
|   - Sidechain Narration Ducking (Envelope Follower, -12 dB Attenuation)           |
+-----------------------------------------------------------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
| Output Packaging & Manifest                                                       |
|   - 48 kHz 24-bit Stereo WAV Mix, MP3 (if requested), Ducked Mix, 4 Stem WAVs     |
|   - PS1 JSON Manifest (Settings, Timings, Provenance, Commercial Licenses)        |
+-----------------------------------------------------------------------------------+
```

---

## Quickstart & Installation

### Option 1: Local Development (Windows / Linux / macOS)

**Prerequisites**: Python 3.11+

```powershell
# 1. Clone repository
git clone https://github.com/incubrix/soundforge-ai.git
cd soundforge-ai

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate   # Linux/macOS: source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the service
uvicorn soundforge.api.app:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser to:
- **Interactive Technical Demonstration UI**: [http://localhost:8000/demo](http://localhost:8000/demo)
- **Interactive OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Service Liveness Probe**: [http://localhost:8000/health](http://localhost:8000/health)

---

### Option 2: Docker Compose (Reproducible Execution)

```bash
docker compose up --build -d
```

The service will automatically start on port `8000` with continuous healthcheck probing.

---

## API Specification

### 1. Create Generation Job
`POST /api/v1/music/jobs`

**Headers**:
- `Idempotency-Key` *(optional)*: Unique string (e.g. UUID) guaranteeing idempotent retries.

**Request Payload**:
```json
{
  "prompt": "Upbeat tech tutorial background music with inspiring synth melody",
  "duration": 12.0,
  "tempo": 120.0,
  "key": "C_major",
  "loopability": false,
  "sample_rate": 48000,
  "target_loudness": -14.0,
  "output_formats": ["wav", "mp3"],
  "seed": 42
}
```

**Response (`HTTP 202 Accepted`)**:
```json
{
  "job_id": "9a2e7bd3-89a8-4b04-b8a5-8dd3a34a9f96",
  "status": "pending",
  "message": "Background music generation job accepted and enqueued.",
  "created_at": "2026-10-15T12:00:00Z",
  "estimated_duration_seconds": 1.5,
  "idempotency_key": "optional-key"
}
```

---

### 2. Poll Job Status
`GET /api/v1/music/jobs/{job_id}`

**Response (`HTTP 200 OK`)**:
```json
{
  "job_id": "9a2e7bd3-89a8-4b04-b8a5-8dd3a34a9f96",
  "status": "completed",
  "progress": 1.0,
  "current_stage": "Completed",
  "created_at": "2026-10-15T12:00:00Z",
  "started_at": "2026-10-15T12:00:00Z",
  "completed_at": "2026-10-15T12:00:01Z",
  "artifacts": {
    "mix_wav": "/api/v1/music/jobs/9a2e7bd3-89a8-4b04-b8a5-8dd3a34a9f96/artifacts/mix.wav",
    "mix_mp3": "/api/v1/music/jobs/9a2e7bd3-89a8-4b04-b8a5-8dd3a34a9f96/artifacts/mix.mp3",
    "stem_drums": "/api/v1/music/jobs/9a2e7bd3-89a8-4b04-b8a5-8dd3a34a9f96/artifacts/stem_drums.wav",
    "stem_bass": "/api/v1/music/jobs/9a2e7bd3-89a8-4b04-b8a5-8dd3a34a9f96/artifacts/stem_bass.wav",
    "stem_chords": "/api/v1/music/jobs/9a2e7bd3-89a8-4b04-b8a5-8dd3a34a9f96/artifacts/stem_chords.wav",
    "stem_melody": "/api/v1/music/jobs/9a2e7bd3-89a8-4b04-b8a5-8dd3a34a9f96/artifacts/stem_melody.wav",
    "manifest_json": "/api/v1/music/jobs/9a2e7bd3-89a8-4b04-b8a5-8dd3a34a9f96/artifacts/manifest.json"
  },
  "manifest": { ... }
}
```

---

### 3. Download Artifacts
`GET /api/v1/music/jobs/{job_id}/artifacts/{filename}`
- Supported filenames: `mix.wav`, `mix.mp3`, `ducked_mix.wav`, `stem_drums.wav`, `stem_bass.wav`, `stem_chords.wav`, `stem_melody.wav`, `manifest.json`.

---

## Automated Batch Test Runner

Execute the automated test suite across diverse musical prompts, durations, and loudness targets:

```powershell
python scripts/batch_runner.py
```

Sample output:
```
================================================================================
 BATCH RUN SUMMARY TABLE
================================================================================
ID      | Status | Target Dur | Act Dur  | Target LUFS | Act LUFS  | Peak dBTP | Recon Err  | Time(s)
--------------------------------------------------------------------------------------------
TC-01   | PASS   | 6.0        | 6.00     | -14.0       | -14.08    | -1.00     | 0.000000   | 0.59   
TC-02   | PASS   | 8.0        | 8.00     | -14.0       | -14.02    | -1.00     | 0.000000   | 0.65   
TC-03   | PASS   | 10.0       | 10.00    | -14.0       | -14.10    | -1.00     | 0.000000   | 0.91   
TC-04   | PASS   | 5.0        | 5.00     | -16.0       | -16.00    | -1.05     | 0.000000   | 0.50   
TC-05   | PASS   | 3.0        | 3.00     | -14.0       | -14.09    | -1.00     | 0.000000   | 0.52   
================================================================================
```

---

## Running Automated Tests

```powershell
pytest -v
```
All 10 test suites covering DSP stem generation, mathematical reconstruction, EBU R128 loudness targeting, True Peak limiting, sidechain ducking, API routes, and idempotency will execute.

---

## Directory Layout

```
soundforge-ai/
├── soundforge/
│   ├── api/             # FastAPI routes, background queue, idempotency, demo UI
│   ├── dsp/             # Multi-stem synthesis, music theory, mixing, mastering, ducking
│   ├── engine/          # High-level pipeline coordinator
│   ├── storage/         # Local & S3-compatible storage providers
│   ├── utils/           # Structured JSON logging
│   ├── config.py        # Settings & environment configuration
│   ├── manifest.py      # PS1 Manifest generator
│   └── models.py        # Pydantic request/response schemas
├── tests/               # Pytest integration & unit test suite
├── scripts/
│   ├── batch_runner.py          # Automated batch test runner
│   └── generate_audio_pack.py   # Reference audio pack generator
├── demo_audio_pack/     # Reference WAV, MP3, stems, and manifests
├── Dockerfile           # Multi-stage production container
├── docker-compose.yml   # Multi-container orchestration
├── requirements.txt     # Locked production dependencies
├── PLAN.md              # Technical design & phased roadmap
├── REPORT.md            # Technical engineering evaluation report
├── SOURCES.md           # Component licensing & provenance audit
└── AI_USE.md            # Assessment AI usage disclosure
```
