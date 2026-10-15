# SoundForge AI: Sources, Component Inventory & Commercial Licensing Audit

This document verifies the commercial-use clearance, provenance, and license compliance for every library, algorithm, synthesis model, and dependency utilized in **SoundForge AI** for the IncuBrix Software Engineer Assessment (Problem Statement PS1).

---

## 1. Commercial Licensing Summary

| Component | Role / Purpose | License | Commercial Use Permitted? |
| :--- | :--- | :--- | :---: |
| **SoundForge Core Engine** | Procedural DSP synthesizer, arranger, and mixer | MIT License | **Yes** |
| **FastAPI** | Web framework and REST API routing | MIT License | **Yes** |
| **Uvicorn** | ASGI server implementation | BSD-3-Clause | **Yes** |
| **Pydantic / Pydantic-Settings** | Data validation and environment settings | MIT License | **Yes** |
| **NumPy** | Vectorized audio array manipulation and synthesis math | BSD-3-Clause | **Yes** |
| **SciPy** | Digital signal processing, Butterworth SOS filters, waveforms | BSD-3-Clause | **Yes** |
| **SoundFile / libsndfile** | Audio file I/O (24-bit PCM WAV, MP3 encoding) | BSD / LGPL-2.1 | **Yes** |
| **Pyloudnorm** | ITU-R BS.1770-4 / EBU R128 loudness measurement | MIT License | **Yes** |
| **HTTPX** | Asynchronous HTTP client for narration download and callbacks | BSD-3-Clause | **Yes** |
| **Pytest / Pytest-Asyncio** | Automated testing harness | MIT License | **Yes** |

---

## 2. Proprietary Assets & Sampling Audit

- **Third-Party Soundfonts**: **NONE USED**. No SF2, SF3, or DLS soundfont files are bundled or loaded. (Many popular soundfonts distributed on the web carry non-commercial Creative Commons CC-BY-NC licenses; therefore, all soundfonts were intentionally omitted).
- **Audio Sample Packs**: **NONE USED**. No copyrighted drum loops, one-shots, vocal samples, or royalty-entangled loops are used.
- **Neural Model Weights**: **NONE USED**. No proprietary weights trained on copyrighted music datasets (e.g. Meta MusicGen under CC-BY-NC, or Suno/Udio proprietary models) are used.
- **Synthesis Equations**: All audio synthesis equations (exponential pitch decay kick, dual-oscillator white noise snare, resonant bandpass hi-hats, subtractive sawtooth/square oscillators, biquad lowpass filters) are derived from published academic DSP literature and public domain mathematical formulations.

---

## 3. Dependency Licensing Details

### 3.1 FastAPI
- **Repository**: [https://github.com/tiangolo/fastapi](https://github.com/tiangolo/fastapi)
- **License**: MIT License
- **Terms**: Permissive commercial use, modification, distribution, and private use.

### 3.2 NumPy & SciPy
- **NumPy Repository**: [https://github.com/numpy/numpy](https://github.com/numpy/numpy) (BSD-3-Clause)
- **SciPy Repository**: [https://github.com/scipy/scipy](https://github.com/scipy/scipy) (BSD-3-Clause)
- **Terms**: Permissive commercial use with copyright notice retention.

### 3.3 SoundFile & libsndfile
- **SoundFile Repository**: [https://github.com/bastibe/python-soundfile](https://github.com/bastibe/python-soundfile) (BSD-3-Clause)
- **libsndfile Library**: [https://github.com/libsndfile/libsndfile](https://github.com/libsndfile/libsndfile) (LGPL-2.1 / BSD)
- **Terms**: Dynamic linking to libsndfile shared library complies with LGPL-2.1; full commercial distribution permitted.

### 3.4 Pyloudnorm
- **Repository**: [https://github.com/csteinmetz1/pyloudnorm](https://github.com/csteinmetz1/pyloudnorm)
- **Author**: Christian Steinmetz
- **License**: MIT License
- **Reference**: ITU-R BS.1770-4 ("Algorithms to measure audio programme loudness and true-peak audio level").

---

## 4. Verification Statement

I hereby certify that all components, algorithms, software dependencies, and DSP modules within the **SoundForge AI** codebase have been audited and verified for unrestricted commercial use. No un-cleared or non-commercial assets are present in this repository.
