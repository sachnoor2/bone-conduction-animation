#!/usr/bin/env python3
import sys, json, subprocess, os
from pathlib import Path

FPS        = 60
VOICE_NAME = "am_fenrir"
SPEED      = 1.0
LANG       = "en-us" # We use the en-us model but feed it Devanagari/Hindi phonetics
AUDIO_DIR  = Path("public/audio")
SEG_DIR    = AUDIO_DIR / "segments"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SEG_DIR.mkdir(parents=True, exist_ok=True)

TOTAL_FRAMES = 2700

# Updated with PURE HINDI (Devanagari) as requested for maximum Hindi preference.
SCENES = [
    { "id": "s01", "fs": 15,   "fe": 175,  "text": "क्या आपने कभी सोचा है कि रिकॉर्डिंग में आपकी आवाज़ अलग क्यों लगती है?" },
    { "id": "s02", "fs": 215,  "fe": 475,  "text": "आपकी आवाज़ दो रास्तों से कानों तक पहुँचती है।" },
    { "id": "s03", "fs": 535,  "fe": 760,  "text": "पहला रास्ता— हवा के ज़रिए।" },
    { "id": "s04", "fs": 790,  "fe": 1060, "text": "दूसरा— आपकी खोपड़ी की हड्डियों के ज़रिए।" },
    { "id": "s05", "fs": 1095, "fe": 1360, "text": "हड्डियाँ low frequency को boost करती हैं।" },
    { "id": "s06", "fs": 1390, "fe": 1640, "text": "Microphone सिर्फ हवा कैप्चर करता है।" },
    { "id": "s07", "fs": 1795, "fe": 1990, "text": "Beethoven... पूरी तरह बहरे थे।" },
    { "id": "s08", "fs": 2020, "fe": 2290, "text": "पर उन्होंने piano को छड़ी से छूकर म्यूज़िक सुना।" },
    { "id": "s09", "fs": 2330, "fe": 2540, "text": "वो भी— bone conduction था।" },
    { "id": "s10", "fs": 2570, "fe": 2680, "text": "आपकी असली आवाज़ वही है जो दूसरे सुनते हैं।" },
]

def main():
    from kokoro_onnx import Kokoro
    import soundfile as sf
    
    model_path = "/tmp/kokoro-v1.0.onnx"
    voices_path = "/tmp/voices-v1.0.bin"
    if not os.path.exists(model_path):
        model_path = "kokoro-v1.0.onnx"
        voices_path = "voices-v1.0.bin"

    print(f"── Generating Hindi Science Narration with Kokoro ──")
    kokoro = Kokoro(model_path, voices_path)
    
    for sc in SCENES:
        print(f"  Synthesizing {sc['id']}...")
        # Note: Kokoro v1.0 ONNX supports multiple languages. We pass Hindi text directly.
        samples, sample_rate = kokoro.create(sc["text"], voice=VOICE_NAME, speed=SPEED, lang="hi")
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
    print("\n✅ Final Hindi Narration complete.")

if __name__ == "__main__":
    main()
