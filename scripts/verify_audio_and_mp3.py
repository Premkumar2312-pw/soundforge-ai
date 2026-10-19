import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import asyncio
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from soundforge.engine.generator import execute_generation_pipeline
from soundforge.models import MusicJobRequest

async def verify_audio_duration_and_reconstruction():
    durations = [5.0, 10.0, 60.0, 300.0]
    out_dir = os.path.abspath("test_output/audio_mp3_verification")
    os.makedirs(out_dir, exist_ok=True)

    meter = pyln.Meter(48000)
    results = []

    print("=== STARTING AUDIO & MP3 VERIFICATION (5s, 10s, 60s, 300s) ===")
    for dur in durations:
        print(f"\n--- Testing Duration: {dur}s ---")
        job_id = f"test-dur-{int(dur)}s"
        job_dir = os.path.join(out_dir, f"dur_{int(dur)}s")
        os.makedirs(job_dir, exist_ok=True)

        req = MusicJobRequest(
            prompt=f"Cinematic corporate technology theme at {dur}s duration",
            duration_s=dur,
            tempo_bpm=120.0,
            seed=42,
            target_lufs=-16.0,
            output_formats=["wav", "mp3"]
        )

        res = await execute_generation_pipeline(job_id=job_id, request=req, output_dir=job_dir)
        print(f"Generation completed for {dur}s in job dir: {job_dir}")

        # 1. Check WAV and MP3 files existence
        wav_path = os.path.join(job_dir, "mix.wav")
        mp3_path = os.path.join(job_dir, "mix.mp3")
        assert os.path.exists(wav_path), f"mix.wav missing for {dur}s"
        assert os.path.exists(mp3_path), f"mix.mp3 missing for {dur}s"
        wav_size = os.path.getsize(wav_path)
        mp3_size = os.path.getsize(mp3_path)
        print(f"File sizes -> mix.wav: {wav_size} bytes, mix.mp3: {mp3_size} bytes")
        assert wav_size > 1000, f"mix.wav too small: {wav_size}"
        assert mp3_size > 1000, f"mix.mp3 too small: {mp3_size}"

        # 2. Decode MP3 and check readability
        mp3_decoded, mp3_sr = sf.read(mp3_path)
        mp3_dur = len(mp3_decoded) / mp3_sr
        print(f"Decoded mix.mp3: sample_rate={mp3_sr}, length={len(mp3_decoded)} samples, duration={mp3_dur:.3f}s")
        assert mp3_sr == 48000, f"MP3 sample rate {mp3_sr} != 48000"

        # 3. Read saved WAV and verify specifications
        wav_data, sr = sf.read(wav_path)
        assert sr == 48000, f"WAV sample rate {sr} != 48000"
        actual_dur = len(wav_data) / sr
        dur_err = abs(actual_dur - dur)
        print(f"Decoded mix.wav: actual_dur={actual_dur:.4f}s, dur_err={dur_err:.4f}s (target={dur}s)")
        assert dur_err <= 0.05, f"Duration error {dur_err} exceeds 0.05s tolerance!"

        # 4. Measure Loudness & True Peak
        measured_lufs = meter.integrated_loudness(wav_data)
        from scipy.signal import resample_poly
        ov = resample_poly(wav_data, 4, 1)
        peak_linear = np.max(np.abs(ov))
        peak_dbtp = 20.0 * np.log10(peak_linear + 1e-12)
        print(f"Loudness: {measured_lufs:.2f} LUFS (target: -16.0 ± 1.0), True Peak: {peak_dbtp:.2f} dBTP (max -1.0 dBTP)")
        assert -17.0 <= measured_lufs <= -15.0, f"Loudness {measured_lufs:.2f} outside [-17.0, -15.0] LUFS"
        assert peak_dbtp <= -0.99, f"True Peak {peak_dbtp:.2f} dBTP exceeds -1.0 dBTP ceiling"

        # 5. Load Manifest & Reconstruct Master from Stems
        manifest_path = os.path.join(job_dir, "manifest.json")
        assert os.path.exists(manifest_path), "manifest.json missing"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        stem_gains = manifest.get("stem_gains") or manifest.get("mix", {}).get("stem_gains", {})
        stems_dict = {}
        for stem_name, gain in stem_gains.items():
            stem_file = os.path.join(job_dir, f"stem_{stem_name}.wav")
            assert os.path.exists(stem_file), f"{stem_file} missing"
            sdata, ssr = sf.read(stem_file)
            assert ssr == 48000
            stems_dict[stem_name] = sdata

        # Sum weighted stems
        reconstructed_mix = np.zeros_like(wav_data)
        for stem_name, gain in stem_gains.items():
            reconstructed_mix += stems_dict[stem_name] * gain

        diff = wav_data - reconstructed_mix
        max_recon_err = float(np.max(np.abs(diff)))
        rms_recon_err = float(np.sqrt(np.mean(diff ** 2)))
        print(f"Stem Reconstruction -> Max Err: {max_recon_err:.2e}, RMS Err: {rms_recon_err:.2e}")
        assert max_recon_err < 1e-5, f"Stem reconstruction max error {max_recon_err} too high!"

        # 6. Verify Stems are Genuine Independent Musical Parts (not frequency split)
        stem_keys = list(stems_dict.keys())
        correlations = {}
        for i in range(len(stem_keys)):
            for j in range(i + 1, len(stem_keys)):
                k1, k2 = stem_keys[i], stem_keys[j]
                s1 = stems_dict[k1][:, 0]
                s2 = stems_dict[k2][:, 0]
                r = float(np.corrcoef(s1, s2)[0, 1])
                correlations[f"{k1}_vs_{k2}"] = r

        print("Stem Pairwise Correlations (independence proof):", {k: f"{v:.3f}" for k, v in correlations.items()})
        for pair, r in correlations.items():
            assert abs(r) < 0.65, f"High stem correlation ({pair}: {r:.2f}) indicates possible leakage/frequency splitting!"

        # Bass stem spectral energy check
        bass_fft = np.abs(np.fft.rfft(stems_dict["bass"][:48000, 0]))
        freqs = np.fft.rfftfreq(48000, 1/48000)
        low_energy = np.sum(bass_fft[freqs < 250])
        total_energy = np.sum(bass_fft)
        bass_low_ratio = low_energy / (total_energy + 1e-12)
        print(f"Bass Low-Frequency Energy Ratio (<250Hz): {bass_low_ratio:.2%}")
        assert bass_low_ratio > 0.60, "Bass stem should be concentrated below 250 Hz"

        results.append({
            "duration": dur,
            "actual_duration": actual_dur,
            "duration_error": dur_err,
            "lufs": measured_lufs,
            "peak_dbtp": peak_dbtp,
            "max_recon_err": max_recon_err,
            "rms_recon_err": rms_recon_err,
            "mp3_decoded_ok": True,
            "correlations": correlations
        })

    print("\n=== ALL AUDIO & MP3 VERIFICATIONS (5s, 10s, 60s, 300s) PASSED SUCCESSFULLY ===")
    return results

if __name__ == "__main__":
    asyncio.run(verify_audio_duration_and_reconstruction())
