#!/usr/bin/env python3
import sys, json, subprocess, os
from pathlib import Path

FPS        = 60
VOICE_NAME = "am_fenrir"
SPEED      = 1.0
LANG       = "en-us"
AUDIO_DIR  = Path("public/audio")
SEG_DIR    = AUDIO_DIR / "segments"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SEG_DIR.mkdir(parents=True, exist_ok=True)

TOTAL_FRAMES = 2700

# Aligning with BoneConduction.tsx SUBS
SCENES = [
    { "id": "s01", "fs": 15,   "fe": 175,  "text": "Tum jo sunte ho — wo tumhari aawaaz nahi hai." },
    { "id": "s02", "fs": 215,  "fe": 475,  "text": "Tumhari aawaaz — do raston se kaano tak pahunchti hai." },
    { "id": "s03", "fs": 535,  "fe": 760,  "text": "Pahla raasta — hawa ke zariye." },
    { "id": "s04", "fs": 790,  "fe": 1060, "text": "Doosra — tumhari khopdi ki haddiyon ke zariye." },
    { "id": "s05", "fs": 1095, "fe": 1360, "text": "Haddiyan low frequency ko boost karti hain." },
    { "id": "s06", "fs": 1390, "fe": 1640, "text": "Microphone sirf hawa capture karta hai." },
    { "id": "s07", "fs": 1795, "fe": 1990, "text": "Beethoven... poori tarah bahre the." },
    { "id": "s08", "fs": 2020, "fe": 2290, "text": "Par unhone piano ko chhaddi se chhukar music suna." },
    { "id": "s09", "fs": 2330, "fe": 2540, "text": "Wo bhi — bone conduction tha." },
    { "id": "s10", "fs": 2570, "fe": 2680, "text": "Tumhari asli aawaaz wahi hai — jo doosre sunte hain." },
]

def main():
    from kokoro_onnx import Kokoro
    import soundfile as sf
    
    model_path = "/tmp/kokoro-v1.0.onnx"
    voices_path = "/tmp/voices-v1.0.bin"
    if not os.path.exists(model_path):
        model_path = "kokoro-v1.0.onnx"
        voices_path = "voices-v1.0.bin"

    print(f"── Generating Bone Conduction scenes with Kokoro ({VOICE_NAME}) ──")
    kokoro = Kokoro(model_path, voices_path)
    
    for sc in SCENES:
        print(f"  Synthesizing {sc['id']}...")
        samples, sample_rate = kokoro.create(sc["text"], voice=VOICE_NAME, speed=SPEED, lang=LANG)
        wav_path = SEG_DIR / f"{sc['id']}.wav"
        sf.write(str(wav_path), samples, sample_rate)
        subprocess.run(["ffmpeg", "-y", "-i", str(wav_path), "-codec:a", "libmp3lame", "-b:a", "192k", str(SEG_DIR / f"{sc['id']}.mp3")], check=True, capture_output=True)
        wav_path.unlink()

    total_s = TOTAL_FRAMES / FPS
    inputs, filter_parts, labels = [], [], []
    for idx, sc in enumerate(SCENES):
        seg = SEG_DIR / f"{sc['id']}.mp3"
        start_ms = int(sc["fs"] / FPS * 1000)
        inputs += ["-i", str(seg)]
        filter_parts.append(f"[{idx}]adelay={start_ms}|{start_ms}[d{idx}]")
        labels.append(f"[d{idx}]")

    fc = ";".join(filter_parts) + ";" + "".join(labels) + f"amix=inputs={len(SCENES)}:normalize=0[out]"
    subprocess.run(["ffmpeg", "-y"] + inputs + ["-filter_complex", fc, "-map", "[out]", "-t", str(total_s), "-b:a", "192k", str(AUDIO_DIR / "narration_final.mp3")], check=True)
    print("\n✅ Bone Conduction Audio pipeline complete.")

if __name__ == "__main__":
    main()
