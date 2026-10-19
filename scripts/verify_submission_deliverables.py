import os
import json
import soundfile as sf

def main():
    submission_files = [
        "README.md",
        "REPORT.md",
        "SOURCES.md",
        "AI_USE.md",
        "GUIDE.md",
        "CONFIGURE.md",
        "openapi.yaml",
        ".env.example",
        "SUBMISSION_CHECKLIST.md"
    ]

    print("=== CHECKING SUBMISSION DOCUMENTS ===")
    for f in submission_files:
        exists = os.path.exists(f)
        size = os.path.getsize(f) if exists else 0
        status = "PASS" if exists else "FAIL"
        print(f"[{status}] {f} ({size} bytes)")
        assert exists, f"Missing {f}"

    print("\n=== CHECKING DEMO AUDIO PACK ARTIFACTS ===")
    demo_packs = ["01_corporate_upbeat", "02_lofi_chill_loop", "03_cinematic_trailer"]
    for pack in demo_packs:
        pack_dir = os.path.join("demo_audio_pack", pack)
        assert os.path.exists(pack_dir), f"Missing {pack_dir}"

        # Check mix.wav
        wav_path = os.path.join(pack_dir, "mix.wav")
        data, sr = sf.read(wav_path)
        dur = len(data) / sr

        # Check mix.mp3
        mp3_path = os.path.join(pack_dir, "mix.mp3")
        mp3_data, mp3_sr = sf.read(mp3_path)

        # Check manifest
        manifest_path = os.path.join(pack_dir, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest = json.load(mf)

        # Check 4 stems
        stems = ["stem_drums.wav", "stem_bass.wav", "stem_chords.wav", "stem_melody.wav"]
        for s in stems:
            spath = os.path.join(pack_dir, s)
            assert os.path.exists(spath), f"Missing {spath}"
            sdata, ssr = sf.read(spath)
            assert ssr == 48000

        print(f"[PASS] {pack}: dur={dur:.2f}s, sr={sr}, MP3={len(mp3_data)/mp3_sr:.2f}s, stems=4, manifest_status={manifest['status']}")

    print("\n=== ALL SUBMISSION FILES & DEMO AUDIO PACK CHECKS PASSED ===")

if __name__ == "__main__":
    main()
