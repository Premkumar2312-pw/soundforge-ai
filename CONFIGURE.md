# SoundForge AI — Configuration Reference (`CONFIGURE.md`)

This document provides a comprehensive reference for all configurable environment variables, application settings, storage backends, and operational modes in **SoundForge AI**.

---

## 1. Quick Start (`.env.example`)

SoundForge AI uses a `.env` file for runtime configuration. For local development, all variables have sensible, production-ready defaults and no API keys or paid external services are required.

```powershell
# Copy example configuration for local execution
Copy-Item .env.example .env
```

---

## 2. Complete Environment Variables Matrix

| Variable | Type | Default | Valid Values | Description |
| :--- | :---: | :---: | :--- | :--- |
| `HOST` | string | `0.0.0.0` | IP Address | Server bind address. |
| `PORT` | integer | `8000` | 1–65535 | Server listen port. |
| `APP_ENV` | string | `production` | `development`, `production`, `test` | Runtime environment mode. |
| `PROVIDER` | string | `procedural` | `procedural`, `mock` | Generation engine provider adapter. `procedural` uses real DSP synthesis; `mock` runs instant zero-compute for testing. |
| `STORAGE_BACKEND` | string | `local` | `local`, `s3` | Artifact storage provider. |
| `STORAGE_DIR` | string | `./storage` | Directory path | Local filesystem directory for generated audio artifacts. |
| `S3_ENDPOINT_URL` | string | *(null)* | URL (e.g. `http://localhost:9000`) | S3 / MinIO compatible API endpoint URL. |
| `S3_ACCESS_KEY` | string | *(null)* | string | S3 Access Key ID (placeholder in `.env.example`). |
| `S3_SECRET_KEY` | string | *(null)* | string | S3 Secret Access Key (placeholder in `.env.example`). |
| `S3_BUCKET_NAME` | string | `soundforge-audio` | Valid S3 bucket | Bucket name where artifacts and manifests are stored. |
| `S3_REGION` | string | `us-east-1` | AWS region code | S3 region identifier. |
| `DEFAULT_SAMPLE_RATE` | integer | `48000` | `44100`, `48000`, `96000` | Default sample rate in Hz (PS1 default is 48 kHz). |
| `DEFAULT_TARGET_LOUDNESS` | float | `-16.0` | `-36.0` to `-6.0` | Default integrated target loudness in LUFS (PS1 default is -16.0 LUFS). |
| `MAX_TRUE_PEAK_DBTP` | float | `-1.0` | `-12.0` to `0.0` | Maximum allowable True Peak level in dBTP (PS1 ceiling is -1.0 dBTP). |
| `MIN_DURATION_SECONDS` | float | `5.0` | `5.0` | Minimum allowable duration in seconds (PS1 boundary). |
| `MAX_DURATION_SECONDS` | float | `300.0` | `300.0` | Maximum allowable duration in seconds (PS1 boundary). |
| `DURATION_TOLERANCE_SECONDS` | float | `0.05` | `0.01` to `0.10` | Maximum allowable duration variance in seconds. |
| `LOUDNESS_TOLERANCE_LU` | float | `1.0` | `0.5` to `2.0` | Permissible loudness deviation in Loudness Units (LU). |
| `CALLBACK_SIGNING_SECRET` | string | `incubrix-secret` | string | Secret key for signing webhook payloads with HMAC-SHA256 (`X-IncuBrix-Signature`). |
| `LOG_LEVEL` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Structured JSON log verbosity. |

---

## 3. Provider Architecture Configuration

SoundForge AI implements an explicit Provider-Adapter interface:

### 3.1 Procedural DSP Provider (Default: `PROVIDER=procedural`)
- **Engine**: 100% offline, zero-API-key procedural digital signal processing engine.
- **Synthesis**: Multi-track synthesis of drums, bass, chords, and melody using mathematical algorithms (exponential pitch sweeps, filtered white noise, bandpass hi-hats, band-limited subtractive oscillators, and biquad low-pass filters).
- **Licensing**: Fully cleared for commercial use under permissive licenses (MIT, BSD-3-Clause).
- **Execution Cost**: Pure local CPU compute (~0.05–0.12s per second of audio on modern x86_64 CPU). Direct API expense: **\$0.00**.

### 3.2 Deterministic Mock Provider (`PROVIDER=mock`)
- **Engine**: Zero-compute deterministic sine synthesizer designed for ultra-fast CI test suites and high-concurrency harness verification.
- **Speed**: Generates valid 48 kHz 24-bit PCM WAV mixes, stems, and manifests in < 0.05 seconds.
- **Failure Simulation**: Supports injecting simulated errors (via prompt substring `__SIMULATE_FAILURE__`) and timeouts (via `__SIMULATE_TIMEOUT__`) to test error handling and recovery mechanisms.

---

## 4. Storage Architecture Configuration

### 4.1 Local Filesystem Storage (`STORAGE_BACKEND=local`)
Artifacts are saved in structured directory trees:
```
./storage/
└── <job_id>/
    ├── mix.wav                  # Master mix (48 kHz, 24-bit PCM)
    ├── mix.mp3                  # MP3 mix (when requested)
    ├── mix_ducked.wav           # Ducked mix (Assessment contract)
    ├── ducked_mix.wav           # Ducked mix (alias)
    ├── music_manifest.json      # Assessment contract manifest
    ├── manifest.json            # Manifest alias
    ├── stem_drums.wav           # Root-level stem
    ├── stem_bass.wav            # Root-level stem
    ├── stem_chords.wav          # Root-level stem
    ├── stem_melody.wav          # Root-level stem
    └── stems/                   # Stems directory
        ├── drums.wav
        ├── bass.wav
        ├── chords.wav
        └── melody.wav
```

### 4.2 S3-Compatible Storage (`STORAGE_BACKEND=s3`)
When using MinIO or AWS S3, configure:
```ini
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=soundforge-audio
S3_REGION=us-east-1
```
The application checks bucket availability during startup and reports readiness via `/ready`.

---

## 5. Security & Safety Controls

- **SSRF Prevention**: `soundforge/dsp/ducking.py` enforces private IP blocking. Requests to loopback addresses (`127.0.0.1`, `localhost`), link-local (`169.254.0.0/16`), and private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) are blocked.
- **Secret Protection**: `.env` and credential files are strictly excluded in `.gitignore`. Secrets are never logged or exposed in manifests.
- **HMAC Callback Signing**: Webhooks are authenticated using an HMAC-SHA256 signature generated with `CALLBACK_SIGNING_SECRET` and transmitted in the `X-IncuBrix-Signature` header.
- **Input Validation**: Prompt length is constrained to 1000 characters; durations are validated within [5.0, 300.0] seconds; unsupported sample rates or formats trigger structured HTTP 422 errors.
