# SoundForge AI: AI Assistance & Disclosure (AI_USE.md)

In accordance with the **IncuBrix Software Engineer Assessment** transparency guidelines, this document provides a comprehensive disclosure of how Artificial Intelligence tools and models were utilized throughout the design, implementation, testing, and documentation of **SoundForge AI**.

---

## 1. Overview of AI Usage

An AI pair programmer (Antigravity with Gemini 3.8 Flash) was utilized as an engineering accelerator to assist in rapid prototyping, DSP algorithm formulation, automated test suite authoring, and documentation structuring.

All engineering decisions, architectural trade-offs, code reviews, and verification checks were directed to ensure strict adherence to the Problem Statement PS1 specification.

---

## 2. Granular Breakdown by Phase

| Phase / Component | AI Role & Assistance | Human / Architectural Oversight |
| :--- | :--- | :--- |
| **Phase 1: Environment & Setup** | Generated initial scaffolding, dependency declarations (`requirements.txt`), and `.gitignore`. | Inspected system toolchains (Python 3.11, Docker, Git) and verified compatibility with Windows PowerShell and Linux Docker environments. |
| **Phase 2: Audio Proof of Concept (PoC)** | Formulated procedural DSP synthesis functions (kick exponential decay, snare bandpass noise, biquad filtering). | Verified acoustic fidelity, verified zero-frequency-splitting policy, and validated that linear mix reconstruction error was mathematically zero. |
| **Phase 3: Core Pipeline & DSP** | Drafted music theory progressions, scale quantization tables, loudness normalization logic (`pyloudnorm`), and sidechain ducking envelope followers. | Validated mathematical identities ($Mix = \sum g_i \cdot Stem_i$), corrected sine-wave zero-crossing test anomalies, and ensured proper stereo panning math. |
| **Phase 4: FastAPI & Background Jobs** | Generated FastAPI endpoints (`/api/v1/music/jobs`), async job manager, and `Idempotency-Key` SHA256 caching. | Reviewed status codes (HTTP 202 Accepted, HTTP 409 Conflict, HTTP 422 Unprocessable Entity), OpenAPI 3.1 schema definitions, and storage provider abstractions. |
| **Phase 5: Docker & Batch Runner** | Authored multi-stage `Dockerfile`, `docker-compose.yml`, and `scripts/batch_runner.py` matrix evaluator. | Verified non-root container security user (`appuser`), healthcheck probe timing, and local storage volume mounting. |
| **Phase 6: Automated Testing** | Drafted unit and integration test assertions across API, DSP, loudness, ducking, and manifest schemas. | Ran `pytest -v`, diagnosed deprecation warnings (migrated from deprecated `@app.on_event` to FastAPI `lifespan` context manager), and ensured 100% test pass rate. |
| **Phase 7: Demo UI & Documentation** | Crafted embedded single-page demonstration UI HTML/JS, `README.md`, `REPORT.md`, `SOURCES.md`, and `AI_USE.md`. | Verified all claims against actual empirical test logs, confirmed commercial licensing terms, and eliminated unsupported assertions. |

---

## 3. Independent Verification & Integrity Safeguards

- **Zero Fabricated Claims**: No benchmark numbers, performance metrics, or licensing rights were fabricated. All numbers reported in `REPORT.md` and `batch_results.json` were derived from actual automated test runs.
- **Strict Prohibition of Frequency Splitting**: Explicit checks were integrated into unit tests (`test_dsp.py`) to confirm that stems originate from separate audio generators with low cross-correlation, rather than split filter bands.
- **Licensing Audit**: Every dependency was cross-referenced with its upstream open-source license to verify commercial clearance.
