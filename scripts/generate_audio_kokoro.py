#!/usr/bin/env python3
import sys, json, subprocess, os
from pathlib import Path

# Kokoro-specific imports would be here if running locally, 
# but this script runs in GitHub Actions.
# We need to ensure the CI environment has the kokoro library.

FPS        = 60
VOICE_NAME = "am_fenrir" # Clear American Male Narrator
SPEED      = 1.0
LANG       = "en-us" # Kokoro v1.0 handles multiple langs, but en-us is most stable for Hinglish mixing
AUDIO_DIR  = Path("public/audio")
SEG_DIR    = AUDIO_DIR / "segments"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SEG_DIR.mkdir(parents=True, exist_ok=True)

TOTAL_FRAMES = 2700

SCENES = [
    {
        "id": "s01", "fs": 0, "fe": 220,
        "text": "Kya aapne kabhi socha hai ki chipkali ki poonch katne ke baad bhi kaise hilti rehti hai?",
    },
    {
        "id": "s02", "fs": 180, "fe": 540,
        "text": "Is phenomenon ko 'Autotomy' kehte hain. Jab koi predator chipkali ko pakadta hai, toh wo apni poonch ke muscles ko zor se contract karke use alag kar deti hai.",
    },
    {
        "id": "s03", "fs": 500, "fe": 1240,
        "text": "Lekin asli magic yahan shuru hota hai. Katne ke baad bhi poonch ke andar ke nerves 'reflex arcs' generate karte hain, jo use 30 minutes tak hilne par majboor karte hain.",
    },
    {
        "id": "s04", "fs": 1200, "fe": 1800,
        "text": "Ye ek distracting survival mechanism hai—jab tak dushman us hilti hui poonch mein uljha reha hai, chipkali gayab ho jati hai.",
    },
    {
        "id": "s05", "fs": 1760, "fe": 2360,
        "text": "Aur sabse hairani ki baat? Uske stem cells kuch hi hafton mein ek nayi poonch uga dete hain!",
    },
    {
        "id": "s06", "fs": 2320, "fe": 2700,
        "text": "Agli baar jab aap ise dekhein, toh yaad rakhein: ye maut nahi, ek smart survival trick hai.",
    },
]

def main():
    # In GitHub Actions, we assume kokoro-onnx is installed and models are downloaded
    from kokoro_onnx import Kokoro
    import soundfile as sf
    
    model_path = "/tmp/kokoro-v1.0.onnx"
    voices_path = "/tmp/voices-v1.0.bin"
    
    if not os.path.exists(model_path):
        # Fallback to current dir if /tmp doesn't have it
        model_path = "kokoro-v1.0.onnx"
        voices_path = "voices-v1.0.bin"

    print(f"── Generating scenes with Kokoro ({VOICE_NAME}) ──")
    kokoro = Kokoro(model_path, voices_path)
    
    for sc in SCENES:
        print(f"  Synthesizing {sc['id']}...")
        samples, sample_rate = kokoro.create(sc["text"], voice=VOICE_NAME, speed=SPEED, lang=LANG)
        wav_path = SEG_DIR / f"{sc['id']}.wav"
        sf.write(str(wav_path), samples, sample_rate)
        
        # Convert to mp3 for Remotion/ffmpeg pipeline consistency
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
    
    manifest = [{"id": s["id"], "text": s["text"], "frame_start": s["fs"], "frame_end": s["fe"]} for s in SCENES]
    (AUDIO_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("\n✅ Kokoro Audio pipeline complete.")

if __name__ == "__main__":
    main()
