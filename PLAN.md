# SoundForge AI: Implementation Plan & Architecture Specification
**Problem Statement PS1: AI Background Music Engine for Video**
**Target**: IncuBrix Software Engineer Assessment

---

## 1. System Architecture Overview

```
                      +------------------------------------------+
                      |               Client / UI                |
                      +--------------------+---------------------+
                                           |
                              POST /api/v1/music/jobs
                              (with Idempotency-Key)
                                           v
+-----------------------------------------------------------------------------------+
| FastAPI Service Layer                                                             |
|   +-----------------------+     +-----------------------+     +-----------------+ |
|   | Job Ingestion &       | --> | Idempotency Store     | --> | Background Task | |
|   | Request Validation    |     | (UUID/Hash Cache)     |     | Manager         | |
|   +-----------------------+     +-----------------------+     +--------+--------+ |
+------------------------------------------------------------------------|----------+
                                                                         v
+-----------------------------------------------------------------------------------+
| Audio Generation & Synthesis Pipeline                                             |
|                                                                                   |
|  +---------------------+   +---------------------+   +--------------------------+ |
|  | Prompt & Section    |-->| Algorithmic Musical |-->| Multi-Stem Synthesizers: | |
|  | Intent Analyzer     |   | Theory Arranger     |   | - Drums Engine           | |
|  | (BPM, Key, Sections)|   | (Chord Progression, |   | - Bassline Synth         | |
|  +---------------------+   |  Bass, Motifs, Rhy) |   | - Harmony / Chords Synth | |
|                            +---------------------+   | - Melody / Lead Synth    | |
|                                                      +------------+-------------+ |
+-------------------------------------------------------------------|---------------+
                                                                    v
+-----------------------------------------------------------------------------------+
| DSP & Audio Engineering Stage                                                     |
|                                                                                   |
|  +------------------------+   +-----------------------+   +---------------------+ |
|  | Stem Mixing & Linear   |-->| Master Bus &          |-->| Sidechain Narration | |
|  | Mathematical Summing   |   | ITU-R BS.1770 / EBU   |   | Ducking Compressor  | |
|  | (Exact Gains)          |   | R128 Loudness Normal. |   | (Envelope Follower) | |
|  +------------------------+   +-----------------------+   +---------------------+ |
+-------------------------------------------------------------------|---------------+
                                                                    v
+-----------------------------------------------------------------------------------+
| Packaging, Verification & Storage                                                 |
|                                                                                   |
|  +------------------------+   +-----------------------+   +---------------------+ |
|  | True Peak & Exact      |-->| Manifest Generator    |-->| Storage Backend     | |
|  | Duration Validator     |   | (Provenance, Gains,   |   | (S3 / Local         | |
|  | (48 kHz WAV, MP3)      |   |  Timing, Licensing)   |   |  Filesystem Store)  | |
|  +------------------------+   +-----------------------+   +---------------------+ |
+-----------------------------------------------------------------------------------+
```

---

## 2. Key Components & Responsibilities

1. **Procedural Multi-Track Synthesis Engine (`soundforge/engine/`)**:
   - **Zero Frequency-Splitting Policy**: True independent generative synthesis per stem.
   - **Drums & Percussion Engine**:
     - Procedural synthesis of Kick (pitch envelope sub-sine), Snare (dual oscillator + high-pass shaped noise burst), Hi-Hat (metallic resonant bandpass noise with closed/open decay), Shaker/Clap.
   - **Bass Engine**:
     - Subtractive/FM bass synthesizer with resonant low-pass filter, key-tracking, pitch-glide, and saturation.
   - **Chords/Harmony Engine**:
     - Polyphonic supersaw / warm electric piano / analog pad voicing generator following harmonic progressions (e.g. ii-V-I, I-V-vi-IV, i-VII-VI-V).
   - **Melody/Lead Engine**:
     - Expressive lead synthesizer with phrase generator, vibrato, scale quantization, arpeggios, and rhythmic call-and-response.
   - **Ending Control**:
     - Seamless loop mode (periodic boundary alignment) vs. Purposeful ending (musical cadence hold, reverb/delay decay, natural fade-out tail).

2. **Mixing & DSP (`soundforge/dsp/`)**:
   - Multi-stem summing with exact documented linear weights ($Mix = \sum g_i \cdot Stem_i$).
   - Master bus limiter & True Peak detector (inter-sample peak headroom $\le -1.0$ dBTP).
   - Loudness normalization to target LUFS (EBU R128 / ITU-R BS.1770-4 via `pyloudnorm`).
   - Sidechain Narration Ducking compressor with adjustable attack ($20$ ms), release ($250$ ms), ducking ratio, and hold time.
   - Exact-duration truncation/padding with anti-click zero-crossing taper.

3. **API & Service Layer (`soundforge/api/`)**:
   - `POST /api/v1/music/jobs`: Asynchronous job creation, HTTP 202 Accepted.
   - `GET /api/v1/music/jobs/{job_id}`: Job status, progress, manifest, and download links.
   - `GET /api/v1/music/jobs/{job_id}/artifacts/{filename}`: Download audio files (WAV, MP3, stems, manifest).
   - `GET /health` & `GET /ready`: Production liveness and readiness probes.
   - OpenAPI 3.1 documentation with full schemas and example payloads.
   - Idempotency key handling with cached results preventing duplicate processing.

4. **Manifest Specification (`soundforge/manifest.py`)**:
   - Musical settings: prompt, duration, tempo (BPM), key/scale, time signature, loopability.
   - Structural sections: section names, start/end times in seconds, start/end bar and beat counts.
   - Stem gains: documented mixing weights per instrument.
   - Provenance & licensing: engine version, provider, seed, licensing terms (100% commercially cleared, zero proprietary samples).
   - Audio engineering metrics: integrated loudness (LUFS), true peak (dBTP), sample rate (48000 Hz), bit depth, channels (stereo).
   - Performance timings: duration of generation, mixing, ducking, total job execution time.

5. **Storage Layer (`soundforge/storage/`)**:
   - S3-compatible storage interface with clean local filesystem fallback.

---

## 3. Phased Implementation Roadmap

- [x] **Phase 1: Environment & Project Setup**:
  - Python 3.11, Docker, Git verification.
  - Setup core dependencies (`requirements.txt`, `.gitignore`).
  - System architecture and roadmap documentation (`PLAN.md`).
- [ ] **Phase 2: Audio Proof of Concept (PoC)**:
  - Implement standalone synthesis script generating drums, bass, chords, and melody.
  - Render 48 kHz stereo WAV stems and reconstructed mix.
  - Verify mathematical stem summation and measure duration/loudness.
  - Verify commercial clearance of synthesis equations.
- [ ] **Phase 3: Core Generation Pipeline & DSP**:
  - Musical theory engine (scales, chords, section progressions).
  - Multi-stem synthesis pipeline with deterministic seed.
  - Loudness normalization (-14 LUFS standard) and true peak limiting.
  - Sidechain narration ducking engine.
  - Manifest generation.
- [ ] **Phase 4: FastAPI Service & Background Jobs**:
  - Background job queue with progress tracking.
  - Idempotency middleware/store.
  - REST endpoints and artifact download streaming.
  - Storage provider abstraction (Local & S3-compatible).
- [ ] **Phase 5: Docker, Configuration, Logging & Batch Runner**:
  - `Dockerfile` (multi-stage, non-root user) and `docker-compose.yml`.
  - Structured JSON logging.
  - Batch test runner script for bulk evaluation.
- [ ] **Phase 6: Automated Testing Suite**:
  - Unit and integration tests (API, DSP, loudness, duration, stems, ducking, idempotency).
  - Edge cases: short/long durations, odd tempos, various keys, loopable vs purposeful endings.
- [ ] **Phase 7: Demonstration UI & Comprehensive Reports**:
  - Modern web UI for interactive testing (stem solo/mute, narration ducking comparison, manifest viewer).
  - `README.md`, `REPORT.md`, `SOURCES.md`, `AI_USE.md`.
- [ ] **Phase 8: End-to-End Clean Verification**:
  - Run full test suite, verify clean docker build and batch runner execution.
