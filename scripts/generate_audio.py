#!/usr/bin/env python3
import sys, json, math, subprocess, time, urllib.request
from pathlib import Path

FPS        = 60
VOICE_NAME = "am_fenrir"
SPEED      = 1.08
LANG       = "hi"
AUDIO_DIR  = Path("public/audio")
SEG_DIR    = AUDIO_DIR / "segments"
MODEL_PATH = Path("/tmp/kokoro-v1.0.onnx")
VOICES_PATH= Path("/tmp/voices-v1.0.bin")
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
        "text": "Lekin asli magic yahan shuru hota hai. Katne ke baad bhi poonch ko andar ke nerves 'reflex arcs' generate karte hain, jo use 30 minutes tak hilne par majboor karte hain.",
    },
    {
        "id": "s04", "fs": 1200, "fe": 1800,
        "text": "Ye ek distracting survival mechanism hai—jab tak dushman us hilti hui poonch mein uljha reha hai, chipkali gayab ho jati hai.",
    },
    {
        "id": "s05", "fs": 1760, "fe": 2360,
        "text": "Aur sabse hairani ki baat? Uske stem cells kuch hi hafton mein ek nayi poonch ugga dete hain!",
    },
    {
        "id": "s06", "fs": 2320, "fe": 2700,
        "text": "Agli baar jab aap ise dekhen, toh yaad rakhein: ye maut nahi, ek smart survival trick hai.",
    },
]

def install():
    subprocess.run([sys.executable, "-m", "pip", "install", "kokoro-onnx", "soundfile", "pydub", "--quiet"], check=True)

def download_model():
    base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
    for path, url in [(MODEL_PATH, f"{base}/kokoro-v1.0.onnx"), (VOICES_PATH, f"{base}/voices-v1.0.bin")]:
        if not path.exists():
            urllib.request.urlretrieve(url, path)

def main():
    install()
    download_model()
    from kokoro_onnx import Kokoro
    import soundfile as sf
    from pydub import AudioSegment
    
    k = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
    
    for sc in SCENES:
        samples, sr = k.create(sc["text"], voice=VOICE_NAME, speed=SPEED, lang=LANG)
        wav_path = SEG_DIR / f"{sc['id']}.wav"
        sf.write(str(wav_path), samples, sr)
        seg = AudioSegment.from_wav(str(wav_path))
        seg = AudioSegment.from_wav(str(wav_path))
        seg.export(str(SEG_DIR / f"{sc['id']}.mp3"), format="mp3", bitrate="192k")
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

if __name__ == "__main__":
    main()
