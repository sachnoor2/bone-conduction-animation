#!/usr/bin/env python3
import sys, json, subprocess, time, os
from pathlib import Path
import urllib.request

FPS        = 60
VOICE_ID   = "pqHfZKP75CvOlQylNhV4"  # Bill - Wise, Mature, Balanced (Narrator style)
AUDIO_DIR  = Path("public/audio")
SEG_DIR    = AUDIO_DIR / "segments"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SEG_DIR.mkdir(parents=True, exist_ok=True)

TOTAL_FRAMES = 2700
XI_API_KEY = os.environ.get("ELEVEN_API_KEY")

SCENES = [
    {
        "id": "s01", "fs": 0, "fe": 220,
        "text": "क्या आपने कभी सोचा है कि छिपकली की पूंछ कटने के बाद भी कैसे हिलती रहती है?",
    },
    {
        "id": "s02", "fs": 180, "fe": 540,
        "text": "इस phenomenon को 'Autotomy' कहते हैं। जब कोई predator छिपकली को पकड़ता है, तो वो अपनी पूंछ के muscles को ज़ोर से contract करके उसे अलग कर देती है।",
    },
    {
        "id": "s03", "fs": 500, "fe": 1240,
        "text": "लेकिन असली magic यहाँ शुरू होता है। कटने के बाद भी पूंछ के अंदर के nerves 'reflex arcs' generate करते हैं, जो उसे 30 minutes तक हिलने पर मजबूर करते हैं।",
    },
    {
        "id": "s04", "fs": 1200, "fe": 1800,
        "text": "ये एक distracting survival mechanism है—जब तक दुश्मन उस हिलती हुई पूंछ में उलझा रहता है, छिपकली गायब हो जाती है।",
    },
    {
        "id": "s05", "fs": 1760, "fe": 2360,
        "text": "और सबसे हैरानी की बात? उसके stem cells कुछ ही हफ़्तों में एक नयी पूंछ उगा देते हैं!",
    },
    {
        "id": "s06", "fs": 2320, "fe": 2700,
        "text": "अगली बार जब आप इसे देखें, तो याद रखें: ये मौत नहीं, एक smart survival trick है।",
    },
]

def synth_scene(sc):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": XI_API_KEY
    }
    data = {
        "text": sc["text"],
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            with open(SEG_DIR / f"{sc['id']}.mp3", "wb") as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"Error synthesizing {sc['id']}: {e}")
        return False

def main():
    if not XI_API_KEY:
        print("Error: ELEVEN_API_KEY not set")
        sys.exit(1)

    print("── Generating scenes with ElevenLabs ──")
    for sc in SCENES:
        print(f"  Synthesizing {sc['id']}...")
        if not synth_scene(sc):
            sys.exit(1)
        time.sleep(0.5) # rate limit safety

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
    print("\n✅ ElevenLabs Audio pipeline complete.")

if __name__ == "__main__":
    main()
