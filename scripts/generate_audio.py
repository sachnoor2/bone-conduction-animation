#!/usr/bin/env python3
import asyncio
import edge_tts
import os
import subprocess
from pathlib import Path

FPS = 60
AUDIO_DIR = Path("public/audio")
SEG_DIR = AUDIO_DIR / "segments"
TOTAL_FRAMES = 2700

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SEG_DIR.mkdir(parents=True, exist_ok=True)

# Native Hindi Script (predominantly Hindi, some English tech terms)
SCENES = [
    { "id": "s01", "fs": 15,   "fe": 175,  "text": "क्या आपने कभी सोचा है कि रिकॉर्डिंग में आपकी आवाज़ इतनी अलग और अजीब क्यों लगती है?" },
    { "id": "s02", "fs": 215,  "fe": 475,  "text": "इसका कारण है कि आपकी आवाज़ आपके कानों तक दो अलग रास्तों से पहुँचती है।" },
    { "id": "s03", "fs": 535,  "fe": 760,  "text": "पहला रास्ता है— हवा के ज़रिए, जिसे दूसरे भी सुनते हैं।" },
    { "id": "s04", "fs": 790,  "fe": 1060, "text": "लेकिन दूसरा रास्ता है— आपकी खोपड़ी की हड्डियों के ज़रिए, जिसे 'Bone Conduction' कहते हैं।" },
    { "id": "s05", "fs": 1095, "fe": 1360, "text": "ये हड्डियाँ low frequencies को बूस्ट करती हैं, जिससे आपको अपनी आवाज़ भारी और गहरी लगती है।" },
    { "id": "s06", "fs": 1390, "fe": 1640, "text": "लेकिन माइक्रोफोन सिर्फ हवा वाली आवाज़ कैप्चर करता है, इसलिए वो आपको पतली लगती है।" },
    { "id": "s07", "fs": 1795, "fe": 1990, "text": "क्या आप जानते हैं? मशहूर संगीतकार बीथोवेन पूरी तरह बहरे होने के बावजूद पियानो बजाते थे।" },
    { "id": "s08", "fs": 2020, "fe": 2290, "text": "वो पियानो को एक छड़ी से छूकर उसकी वाइब्रेशन को अपनी हड्डियों से महसूस करते थे।" },
    { "id": "s09", "fs": 2330, "fe": 2540, "text": "ये भी 'Bone Conduction' का ही एक कमाल था।" },
    { "id": "s10", "fs": 2570, "fe": 2680, "text": "तो याद रखिए, आपकी असली आवाज़ वही है जो रिकॉर्डिंग में सुनाई देती है।" },
]

VOICES = {
    "Madhur": "hi-IN-MadhurNeural", # Professional Male
    "Swara": "hi-IN-SwaraNeural"    # Professional Female
}

async def generate_scenes(voice_key, voice_id):
    print(f"── Generating Narration with {voice_key} ({voice_id}) ──")
    v_dir = SEG_DIR / voice_key
    v_dir.mkdir(parents=True, exist_ok=True)
    for sc in SCENES:
        print(f"  Synthesizing {sc['id']} for {voice_key}...")
        communicate = edge_tts.Communicate(sc["text"], voice_id, rate="+10%")
        await communicate.save(str(v_dir / f"{sc['id']}.mp3"))

def combine_audio(voice_key):
    v_dir = SEG_DIR / voice_key
    total_s = TOTAL_FRAMES / FPS
    inputs, filter_parts, labels = [], [], []
    for idx, sc in enumerate(SCENES):
        seg = v_dir / f"{sc['id']}.mp3"
        start_ms = int(sc["fs"] / FPS * 1000)
        inputs += ["-i", str(seg)]
        filter_parts.append(f"[{idx}]adelay={start_ms}|{start_ms}[d{idx}]")
        labels.append(f"[d{idx}]")

    fc = ";".join(filter_parts) + ";" + "".join(labels) + f"amix=inputs={len(SCENES)}:normalize=0[out]"
    output_path = AUDIO_DIR / f"narration_{voice_key.lower()}.mp3"
    subprocess.run(["ffmpeg", "-y"] + inputs + ["-filter_complex", fc, "-map", "[out]", "-t", str(total_s), "-b:a", "192k", str(output_path)], check=True)
    print(f"✅ {voice_key} Audio pipeline complete: {output_path}")

async def main():
    # We add a clear console announcement and a small pause to keep them distinct
    print("\n🚀 STARTING NARRATOR 1: MADHUR (Azure Native Hindi Male)")
    await generate_scenes("Madhur", VOICES["Madhur"])
    combine_audio("Madhur")
    print("✅ Madhur version complete. Waiting 10 seconds before starting next...")
    await asyncio.sleep(10)

    print("\n🚀 STARTING NARRATOR 2: SWARA (Azure Native Hindi Female)")
    await generate_scenes("Swara", VOICES["Swara"])
    combine_audio("Swara")
    print("✅ Swara version complete.")

if __name__ == "__main__":
    asyncio.run(main())
