# SoundForge AI — Local Setup Guide (Windows)

This guide walks you through setting up and running **SoundForge AI** on Windows from scratch.
No GPU is required. No API keys or paid services are needed — the engine is 100% local DSP synthesis.

---

## Prerequisites

| Tool | Minimum Version | Check command |
|------|----------------|---------------|
| Python | 3.11+ | `python --version` |
| Git | Any recent | `git --version` |
| Docker Desktop | 4.x+ (optional) | `docker --version` |

### Install Python 3.11
Download from https://www.python.org/downloads/windows/  
During install: **check "Add Python to PATH"**.

### Install Git
Download from https://git-scm.com/download/win and install with defaults.

### Install Docker Desktop (optional, for Docker mode)
Download from https://www.docker.com/products/docker-desktop/  
Start Docker Desktop and wait until the whale icon shows "Docker Desktop is running".

---

## Clone the Repository

```powershell
git clone https://github.com/Premkumar2312-pw/soundforge-ai.git
Set-Location soundforge-ai
```

---

## Set Up the Python Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\Activate.ps1
```

> **Tip**: If you see an execution policy error, run this once in an elevated PowerShell:  
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

Verify activation — your prompt should show `(venv)`.

---

## Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs FastAPI, uvicorn, pyloudnorm, soundfile, numpy, scipy, pydantic, and all other libraries.
Expect ~2–4 minutes on first install.

---

## Environment Variables

SoundForge AI reads configuration from a `.env` file. **No API keys are required** for local operation.

Copy the example file and edit if needed:
```powershell
Copy-Item .env.example .env
```

For local development the defaults are fine — you do not need to change anything.

**Key defaults** (all in `.env.example`):
| Variable | Default | Notes |
|----------|---------|-------|
| `HOST` | `0.0.0.0` | Listen address |
| `PORT` | `8000` | HTTP port |
| `STORAGE_BACKEND` | `local` | Local disk (no S3 needed) |
| `STORAGE_DIR` | `./storage` | Output directory |
| `DEFAULT_SAMPLE_RATE` | `48000` | 48 kHz per PS1 spec |
| `DEFAULT_TARGET_LOUDNESS` | `-16.0` | EBU R128 / PS1 default |
| `LOG_LEVEL` | `INFO` | Structured JSON logs |

For S3-compatible storage (optional), set:
```
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=soundforge-audio
```

---

## Start the Application (without Docker)

```powershell
uvicorn soundforge.api.app:app --host 0.0.0.0 --port 8000 --reload
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Application URLs

| URL | Purpose |
|-----|---------|
| http://localhost:8000/demo | Interactive demo UI |
| http://localhost:8000/docs | Swagger / OpenAPI 3.1 docs |
| http://localhost:8000/redoc | ReDoc API reference |
| http://localhost:8000/health | Liveness probe (`{"status": "ok"}`) |
| http://localhost:8000/ready | Readiness probe |

---

## Generate a Track via API

Open a **second** PowerShell window (keep the server running in the first).

### Submit a job
```powershell
$body = @{
    prompt = "Upbeat corporate background music with inspiring melody"
    duration = 10.0
    tempo = 120.0
    key = "C_major"
    output_formats = @("wav", "mp3")
    seed = 42
} | ConvertTo-Json

$resp = Invoke-RestMethod -Method POST `
    -Uri http://localhost:8000/api/v1/music/jobs `
    -ContentType "application/json" `
    -Body $body

$resp | ConvertTo-Json
$jobId = $resp.job_id
Write-Host "Job ID: $jobId"
```

### Poll job status
```powershell
# Poll until completed
do {
    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/music/jobs/$jobId"
    Write-Host "Status: $($status.status) | Progress: $($status.progress)"
    Start-Sleep 1
} while ($status.status -notin @("completed", "failed"))
```

### Download the mix
```powershell
Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/music/jobs/$jobId/artifacts/mix.wav" `
    -OutFile "my_track.wav"
Write-Host "Downloaded my_track.wav"
```

### Download stems
```powershell
foreach ($stem in @("stem_drums", "stem_bass", "stem_chords", "stem_melody")) {
    Invoke-WebRequest `
        -Uri "http://localhost:8000/api/v1/music/jobs/$jobId/artifacts/$stem.wav" `
        -OutFile "$stem.wav"
    Write-Host "Downloaded $stem.wav"
}
```

### Inspect the manifest
```powershell
$manifest = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/music/jobs/$jobId/artifacts/manifest.json"
$manifest | ConvertTo-Json -Depth 10
```

### Using an Idempotency Key
```powershell
$idemResp = Invoke-RestMethod -Method POST `
    -Uri http://localhost:8000/api/v1/music/jobs `
    -ContentType "application/json" `
    -Headers @{"Idempotency-Key" = "my-unique-key-001"} `
    -Body $body
# Sending the same key again returns the existing job (HTTP 200/409)
```

---

## Docker Compose (Reproducible Container)

### Build and start
```powershell
docker compose up --build -d
```

### Check health
```powershell
Invoke-RestMethod http://localhost:8000/health
```

### View logs
```powershell
docker compose logs -f soundforge-api
```

### Stop
```powershell
docker compose down
```

### Generated audio files location (inside container)
Files are written to `./storage/` on the host (mounted as a volume).

---

## Run the Automated Test Suite

```powershell
python -m pytest tests/ -v
```

Expected output:
```
tests/test_api.py::test_health_and_readiness_endpoints PASSED
tests/test_api.py::test_duration_boundary_and_input_validation PASSED
tests/test_api.py::test_correlation_id_propagation PASSED
tests/test_api.py::test_job_lifecycle_idempotency_and_reconstruction PASSED
tests/test_dsp.py::test_genuine_multi_stem_synthesis PASSED
tests/test_dsp.py::test_exact_linear_stem_reconstruction PASSED
tests/test_dsp.py::test_deterministic_seed_reproducibility PASSED
tests/test_dsp.py::test_saved_disk_files_stem_reconstruction PASSED
tests/test_ducking.py::test_sidechain_ducking_attenuation PASSED
tests/test_manifest.py::test_manifest_schema_completeness PASSED
tests/test_mastering_and_loudness.py::test_mastering_loudness_targeting_ps1_default PASSED
tests/test_mastering_and_loudness.py::test_mastering_custom_target_loudness PASSED
tests/test_mastering_and_loudness.py::test_mastering_high_peak_limiting PASSED

13 passed in ~10s
```

---

## Run the Batch Test Runner

The batch runner tests 7 scenarios including boundary durations, narration ducking, and rejection cases:

```powershell
python scripts/batch_runner.py
```

Test cases covered:
| Case | Scenario | Duration |
|------|----------|----------|
| TC-01 | Minimum boundary | 5 s |
| TC-02 | Lo-fi short | 10 s |
| TC-03 | Cinematic with custom sections | 60 s |
| TC-04 | Ambient medium | 180 s |
| TC-05 | Maximum boundary | 300 s |
| TC-06 | Narration ducking (8 s) | 8 s |
| TC-07 | Below minimum (4 s) → expect 422 | — |

---

## Generate the Demo Audio Pack

```powershell
python scripts/generate_audio_pack.py
```

This creates representative WAV, MP3 and stem files with manifests in `demo_audio_pack/`.

---

## Common Errors and Fixes

### `ModuleNotFoundError: No module named 'soundforge'`
You are not in the project root. Navigate to `c:\Users\ELCOT\projects\soundforge-ai` and re-activate the virtual environment.

### `uvicorn: command not found`
Virtual environment is not activated. Run `venv\Scripts\Activate.ps1` first.

### Port 8000 already in use
```powershell
# Find the process using port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
# Then kill it:
Stop-Process -Id <PID> -Force
```
Or change the port: `uvicorn soundforge.api.app:app --port 8001`

### `libsndfile` error on import of soundfile
Install the binary:
```powershell
pip install soundfile --force-reinstall
```

### Docker: `Cannot connect to the Docker daemon`
Open **Docker Desktop** from the Start menu and wait for it to fully start (whale icon in system tray).

### Docker: `docker compose` not found
Older Docker installations use `docker-compose` (with hyphen). Try:
```powershell
docker-compose up --build -d
```

### Execution policy error when activating venv
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Verify the Application is Ready

```powershell
# Health check
Invoke-RestMethod http://localhost:8000/health
# Expected: { status: "ok", ... }

# Readiness check
Invoke-RestMethod http://localhost:8000/ready
# Expected: { status: "ready", ... }

# Quick smoke test (5-second track)
$body = '{"prompt":"test","duration":5.0}'
Invoke-RestMethod -Method POST -Uri http://localhost:8000/api/v1/music/jobs -ContentType "application/json" -Body $body
```

---

## Git Workflow

### Check status and stage changes
```powershell
git status
git add .
git diff --cached --stat
```

### Commit
```powershell
git commit -m "feat: describe your change"
```

### View history
```powershell
git log --oneline -10
```

### First push to your private GitHub repository
```powershell
# Verify remote is correct
git remote -v

# Push main branch and set upstream tracking
git push --set-upstream origin main
```

You will be prompted for your GitHub username and a **Personal Access Token** (not your password).  
Create a token at: https://github.com/settings/tokens → New classic token → scope: `repo`.

---

## Storage Layout

Generated audio files are stored in `./storage/<job_id>/`:
```
storage/
└── <job_id>/
    ├── mix.wav           # Master mix (48 kHz, 32-bit float)
    ├── mix.mp3           # MP3 (if requested)
    ├── ducked_mix.wav    # Mix with narration ducking applied (if narration_url supplied)
    ├── stem_drums.wav
    ├── stem_bass.wav
    ├── stem_chords.wav
    ├── stem_melody.wav
    └── manifest.json     # Full PS1 manifest
```

---

## API Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/music/jobs` | Submit generation job (HTTP 202) |
| `GET` | `/api/v1/music/jobs/{job_id}` | Poll status and progress |
| `GET` | `/api/v1/music/jobs/{job_id}/artifacts/{file}` | Download artifact |
| `GET` | `/health` | Liveness probe |
| `GET` | `/ready` | Readiness probe |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/demo` | Interactive demo UI |
