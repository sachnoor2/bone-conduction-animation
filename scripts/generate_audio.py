#!/usr/bin/env python3
"""
generate_audio.py
─────────────────
Generates Hindi narration using ElevenLabs API.
Voice: Liam (TX3LPaxmHKxFdv7VOQHJ) — Energetic, young male, social media creator.
Best match for fast-paced Hindi science explainer.

Each scene gets its own MP3 segment, placed precisely at its visual frame_start.
Final assembly → public/audio/narration_final.mp3

Usage (in GitHub Actions):
    ELEVENLABS_API_KEY=xxx python scripts/generate_audio.py
"""

import os, sys, json, math, time, subprocess, struct
from pathlib import Path

FPS = 60
VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"   # Liam — Energetic young male
MODEL_ID  = "eleven_multilingual_v2"  # Best for Hindi

# ── SCENE MANIFEST ────────────────────────────────────────────────
# frame_start / frame_end align exactly with subtitle timeline in BoneConduction.tsx
SCENES = [
    {
        "id": "s01",
        "frame_start": 15, "frame_end": 175,
        "text": "तुम जो सुनते हो... वो तुम्हारी असली आवाज़ नहीं है।",
    },
    {
        "id": "s02",
        "frame_start": 215, "frame_end": 475,
        "text": "तुम्हारी आवाज़ — तुम तक दो रास्तों से पहुँचती है।",
    },
    {
        "id": "s03",
        "frame_start": 535, "frame_end": 900,
        "text": "पहला — Air Conduction। Sound waves हवा में travel करती हैं, Ear तक पहुँचती हैं। Microphone यही record करता है।",
    },
    {
        "id": "s04",
        "frame_start": 790, "frame_end": 1360,
        "text": "दूसरा — Bone Conduction। Skull की हड्डियाँ... vibration को directly Cochlea तक ले जाती हैं। हड्डियाँ low frequency boost करती हैं। इसीलिए अपनी आवाज़ — तुम्हें rich लगती है।",
    },
    {
        "id": "s05",
        "frame_start": 1390, "frame_end": 1640,
        "text": "Microphone सिर्फ हवा capture करता है। Bone path miss हो जाता है। इसीलिए recording में — तुम पतले लगते हो।",
    },
    {
        "id": "s06",
        "frame_start": 1795, "frame_end": 2290,
        "text": "Beethoven... पूरी तरह बहरे थे। जबड़े से छड़ी लगाकर piano feel किया। हड्डियाँ सुन रही थीं।",
    },
    {
        "id": "s07",
        "frame_start": 2330, "frame_end": 2540,
        "text": "तुम्हारी असली आवाज़ वही है — जो दूसरे सुनते हैं।",
    },
    {
        "id": "s08",
        "frame_start": 2570, "frame_end": 2680,
        "text": "Comment करो — क्या तुम्हें अपनी recording पसंद है?",
    },
]

TOTAL_FRAMES = 2700
OUT_DIR = Path("public/audio")
SEG_DIR = OUT_DIR / "segments"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SEG_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.environ["ELEVENLABS_API_KEY"]
HEADERS = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json",
}

# Voice settings — energetic, fast-paced but clear
VOICE_SETTINGS = {
    "stability": 0.38,          # lower = more dynamic/expressive
    "similarity_boost": 0.82,
    "style": 0.55,              # moderate style exaggeration
    "use_speaker_boost": True,
}


def install_deps():
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pydub", "requests", "--quiet"],
        check=True,
    )


def get_mp3_duration_ms(path: Path) -> float:
    """Estimate MP3 duration using mutagen if available, else ffprobe."""
    try:
        import subprocess as sp
        result = sp.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True
        )
        return float(result.stdout.strip()) * 1000
    except Exception:
        return 0.0


def synth_scene(scene: dict, out_path: Path, retries: int = 3) -> bool:
    """Call ElevenLabs TTS API for one scene. Returns True on success."""
    import requests

    if out_path.exists() and out_path.stat().st_size > 1000:
        print(f"  ↩  Cached: {out_path.name}")
        return True

    payload = {
        "text": scene["text"],
        "model_id": MODEL_ID,
        "voice_settings": VOICE_SETTINGS,
    }

    for attempt in range(1, retries + 1):
        print(f"  🎙  [{scene['id']}] attempt {attempt}: {scene['text'][:45]}...")
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
            headers=HEADERS,
            json=payload,
            stream=True,
        )
        if resp.status_code == 200:
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=4096):
                    f.write(chunk)
            print(f"  ✓  {out_path.name}  ({out_path.stat().st_size//1024} KB)")
            return True
        else:
            print(f"  ✗  HTTP {resp.status_code}: {resp.text[:120]}")
            if attempt < retries:
                time.sleep(2 * attempt)

    return False


def assemble(scenes: list):
    """
    Place each segment at its exact frame_start timestamp.
    Gaps are silence. Output: narration_final.mp3
    """
    from pydub import AudioSegment

    total_ms = math.ceil(TOTAL_FRAMES / FPS * 1000)   # 45000 ms
    timeline  = AudioSegment.silent(duration=total_ms, frame_rate=44100)

    for scene in scenes:
        seg_path = SEG_DIR / f"{scene['id']}.mp3"
        if not seg_path.exists():
            print(f"  ⚠  Missing {seg_path.name}, skipping")
            continue

        seg = AudioSegment.from_mp3(str(seg_path))
        start_ms = int(scene["frame_start"] / FPS * 1000)
        timeline  = timeline.overlay(seg, position=start_ms)
        print(f"  ▶  {scene['id']} placed at {start_ms}ms")

    out_path = OUT_DIR / "narration_final.mp3"
    timeline.export(str(out_path), format="mp3", bitrate="192k")
    print(f"\n✓  Final audio → {out_path}  ({total_ms/1000:.1f}s, {out_path.stat().st_size//1024} KB)")

    # Write manifest for AI sync-checker
    manifest = [
        {
            "id": s["id"],
            "text": s["text"],
            "frame_start": s["frame_start"],
            "frame_end": s["frame_end"],
            "time_start_s": round(s["frame_start"] / FPS, 3),
            "time_end_s":   round(s["frame_end"]   / FPS, 3),
            "seg_file": f"segments/{s['id']}.mp3",
            "approved": False,   # sync-checker will set True
        }
        for s in scenes
    ]
    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"✓  manifest.json → {manifest_path}")


def main():
    install_deps()
    print("\n── Generating scene segments via ElevenLabs ──\n")

    failed = []
    for scene in SCENES:
        out_path = SEG_DIR / f"{scene['id']}.mp3"
        ok = synth_scene(scene, out_path)
        if not ok:
            failed.append(scene["id"])
        time.sleep(0.4)   # small delay to be nice to API

    if failed:
        print(f"\n⚠  Failed scenes: {failed}")
        sys.exit(1)

    print("\n── Assembling final audio ──\n")
    assemble(SCENES)
    print("\n✅  Audio pipeline complete.\n")


if __name__ == "__main__":
    main()
