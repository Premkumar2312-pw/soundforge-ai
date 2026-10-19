# SoundForge AI — Comprehensive Operations Guide (`GUIDE.md`)

This guide provides step-by-step instructions for running, testing, demonstrating, and operating **SoundForge AI** on Windows and via Docker Compose.

---

## 1. System Requirements

| Requirement | Minimum | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 / 11 (64-bit) | Windows 11 (64-bit) |
| **Python** | Python 3.11.x | Python 3.11.9+ |
| **Memory (RAM)** | 4 GB | 8 GB+ |
| **Disk Space** | 2 GB free | 5 GB free |
| **GPU** | None required | None (Engine is 100% CPU DSP) |
| **Container Engine** | Docker Desktop 4.x (optional) | Docker Desktop 4.x with WSL2 |

---

## 2. Windows Local Execution (Fewer Than 10 Commands)

Open Windows PowerShell (Run as Administrator or standard user):

```powershell
# 1. Navigate to project root
cd C:\Users\ELCOT\projects\soundforge-ai

# 2. Activate virtual environment (if not already active)
venv\Scripts\Activate.ps1

# 3. Install/verify dependencies
pip install -r requirements.txt

# 4. Copy configuration template
Copy-Item .env.example .env

# 5. Run automated test suite (19 unit/integration tests)
python -m pytest tests/ -v

# 6. Run comprehensive 10-prompt batch runner
python scripts/batch_runner.py --suite ten_prompts

# 7. Start the FastAPI application
uvicorn soundforge.api.app:app --host 0.0.0.0 --port 8000
```

Once started:
- **Interactive Demonstration UI**: [http://localhost:8000/demo](http://localhost:8000/demo)
- **OpenAPI 3.1 Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Interactive Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Liveness Probe**: [http://localhost:8000/health](http://localhost:8000/health)
- **Readiness Probe**: [http://localhost:8000/ready](http://localhost:8000/ready)

---

## 3. Docker Compose Execution

To start the reproducible containerized service:

```powershell
# Build and start container in background
docker compose up --build -d

# Check service health and logs
docker compose logs -f soundforge-api

# Check readiness probe
Invoke-RestMethod http://localhost:8000/ready

# Stop services when finished
docker compose down
```

---

## 4. API End-to-End Walkthrough (PowerShell)

### Step 1: Submit Generation Job (HTTP 202)
```powershell
$body = @{
    prompt = "Upbeat tech corporate background music with inspiring melody"
    duration_s = 15.0
    tempo_bpm = 120.0
    key = "G_major"
    loopable = $true
    output = @{
        sample_rate = 48000
        target_lufs = -16.0
        formats = @("wav", "mp3")
    }
    seed = 42
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod -Method POST `
    -Uri "http://localhost:8000/api/v1/music/jobs" `
    -ContentType "application/json" `
    -Headers @{"Idempotency-Key" = "demo-run-001"} `
    -Body $body

$jobId = $response.job_id
Write-Host "Created Job ID: $jobId"
```

### Step 2: Poll Progress & Status
```powershell
do {
    Start-Sleep -Seconds 1
    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/jobs/$jobId"
    Write-Host "Stage: $($status.current_stage) | Progress: $($status.progress_percent)%"
} while ($status.status -notin @("succeeded", "completed", "failed"))
```

### Step 3: Inspect Manifest & Audio Metrics
```powershell
$manifest = $status.manifest
Write-Host "Target Duration: $($manifest.request_parameters.target_duration_seconds)s"
Write-Host "Actual Duration: $($manifest.audio_metrics.actual_duration_seconds)s"
Write-Host "Measured Loudness: $($manifest.audio_metrics.measured_loudness_lufs) LUFS"
Write-Host "True Peak: $($manifest.audio_metrics.true_peak_dbtp) dBTP"
Write-Host "Max Reconstruction Error: $($manifest.reconstruction_verification.max_reconstruction_error)"
```

### Step 4: Download Master Mix and Separate Stems
```powershell
# Download master mix
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/jobs/$jobId/artifacts/mix.wav" -OutFile "mix.wav"

# Download 4 genuine stems
foreach ($stem in @("drums", "bass", "chords", "melody")) {
    Invoke-WebRequest -Uri "http://localhost:8000/api/v1/jobs/$jobId/artifacts/stem_$stem.wav" -OutFile "stem_$stem.wav"
}

# Download manifest
Invoke-WebRequest -Uri "http://localhost:8000/api/v1/jobs/$jobId/artifacts/music_manifest.json" -OutFile "music_manifest.json"
Write-Host "All artifacts successfully downloaded."
```

---

## 5. Troubleshooting & FAQ

### Port 8000 already in use
```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Stop-Process -Id <PID> -Force
```

### Execution Policy Error on venv activation
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Docker Daemon Not Running
Ensure Docker Desktop is launched and the status indicator in the taskbar tray displays "Docker Desktop is running".

### MP3 Generation on Systems without libmp3lame
The engine uses standard `libsndfile` MP3 encoding. If your host lacks MP3 encoder libraries, SoundForge AI logs an informative warning, ensures the 48 kHz 24-bit PCM WAV mix and stems are successfully delivered, and preserves mathematical reconstruction.
