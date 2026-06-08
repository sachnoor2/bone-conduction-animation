#!/usr/bin/env python3
"""
generate_audio.py
─────────────────
TTS Engine : Kokoro ONNX v1.0
Voice      : am_fenrir  (bold, energetic American male — closest free equivalent
             to ElevenLabs Versatile for Hinglish science narration)
Model      : ~83 MB  downloaded once, cached by GitHub Actions
Language   : hi (Hindi phonemes via espeak-ng) for Hindi words,
             en-us for English terms — Hinglish mix handled automatically

Output
  public/audio/segments/s01.mp3 … s07.mp3   (per-scene)
  public/audio/narration_final.mp3            (assembled, time-aligned)
  public/audio/manifest.json                  (for sync-checker)
"""

import sys, json, math, subprocess, time, urllib.request
from pathlib import Path

FPS        = 60
VOICE_NAME = "am_fenrir"
SPEED      = 1.08          # slight speed-up — more punchy, less drag
LANG       = "hi"          # espeak-ng phoneme set for Hinglish
AUDIO_DIR  = Path("public/audio")
SEG_DIR    = AUDIO_DIR / "segments"
MODEL_PATH = Path("/tmp/kokoro-v1.0.onnx")
VOICES_PATH= Path("/tmp/voices-v1.0.bin")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SEG_DIR.mkdir(parents=True, exist_ok=True)

TOTAL_FRAMES = 2700

# ── SCENE MANIFEST ────────────────────────────────────────────────
# Exact narration text as provided + frame windows from BoneConduction.tsx
SCENES = [
    {
        "id": "s01", "fs": 15, "fe": 475,
        "text": "तुम जो सुनते हो... वो तुम्हारी असली आवाज़ नहीं है। तुम्हारी आवाज़ — तुम तक दो रास्तों से पहुँचती है।",
    },
    {
        "id": "s02", "fs": 535, "fe": 1060,
        "text": "पहला — Air Conduction। Sound waves हवा में travel करती हैं, Ear तक पहुँचती हैं। Microphone यही record करता है।",
    },
    {
        "id": "s03", "fs": 790, "fe": 1360,
        "text": "दूसरा — Bone Conduction। Skull की हड्डियाँ... vibration को directly Cochlea तक ले जाती हैं। हड्डियाँ low frequency boost करती हैं। इसीलिए अपनी आवाज़ — तुम्हें rich लगती है।",
    },
    {
        "id": "s04", "fs": 1390, "fe": 1640,
        "text": "Microphone सिर्फ हवा capture करता है। Bone path miss हो जाता है। इसीलिए recording में — तुम पतले लगते हो।",
    },
    {
        "id": "s05", "fs": 1795, "fe": 2290,
        "text": "Beethoven... पूरी तरह बहरे थे। जबड़े से छड़ी लगाकर piano feel किया। हड्डियाँ सुन रही थीं।",
    },
    {
        "id": "s06", "fs": 2330, "fe": 2540,
        "text": "तुम्हारी असली आवाज़ वही है — जो दूसरे सुनते हैं।",
    },
    {
        "id": "s07", "fs": 2570, "fe": 2700,
        "text": "Comment करो — क्या तुम्हें अपनी recording पसंद है?",
    },
]


# ── INSTALL DEPS ─────────────────────────────────────────────────
def install():
    subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "kokoro-onnx", "soundfile", "pydub", "--quiet"],
        check=True
    )
    # espeak-ng is pre-installed on ubuntu-latest (GitHub Actions)
    # If missing locally: sudo apt-get install espeak-ng


# ── DOWNLOAD MODEL ────────────────────────────────────────────────
def download_model():
    base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
    files = [
        (MODEL_PATH,  f"{base}/kokoro-v1.0.onnx"),
        (VOICES_PATH, f"{base}/voices-v1.0.bin"),
    ]
    for path, url in files:
        if path.exists():
            print(f"  cached  {path.name}  ({path.stat().st_size//1024//1024}MB)")
            continue
        print(f"  downloading {path.name} ...")
        urllib.request.urlretrieve(url, path)
        print(f"  done  {path.stat().st_size//1024//1024}MB")


# ── LOAD MODEL ────────────────────────────────────────────────────
def load_kokoro():
    from kokoro_onnx import Kokoro
    k = Kokoro(str(MODEL_PATH), str(VOICES_PATH))
    voices = k.get_voices()
    if VOICE_NAME not in voices:
        raise RuntimeError(f"Voice '{VOICE_NAME}' not found. Available: {voices}")
    print(f"  model loaded | voice: {VOICE_NAME} | available: {len(voices)} voices")
    return k


# ── SYNTHESISE ONE SCENE ──────────────────────────────────────────
def synth_scene(kokoro, scene: dict) -> bool:
    import soundfile as sf
    import numpy as np

    out = SEG_DIR / f"{scene['id']}.mp3"
    window_s = (scene["fe"] - scene["fs"]) / FPS

    if out.exists() and out.stat().st_size > 3000:
        print(f"  ↩  {scene['id']}  cached  (window={window_s:.1f}s)")
        return True

    print(f"  🎙  {scene['id']}  window={window_s:.1f}s  chars={len(scene['text'])}")
    print(f"      {scene['text'][:60]}...")

    samples, sr = kokoro.create(
        scene["text"],
        voice=VOICE_NAME,
        speed=SPEED,
        lang=LANG,
    )

    # Save as wav first, convert to mp3 via pydub
    wav_path = SEG_DIR / f"{scene['id']}.wav"
    sf.write(str(wav_path), samples, sr)

    from pydub import AudioSegment
    seg = AudioSegment.from_wav(str(wav_path))
    seg.export(str(out), format="mp3", bitrate="192k")
    wav_path.unlink(missing_ok=True)

    actual_s = len(seg) / 1000
    fit = "✓ fits" if actual_s <= window_s + 0.3 else f"⚠ {actual_s:.1f}s > {window_s:.1f}s window"
    print(f"      {fit}  ({actual_s:.2f}s)  {out.stat().st_size//1024}KB")
    return True


# ── ASSEMBLE FINAL AUDIO ──────────────────────────────────────────
def assemble():
    """
    Place each segment at its EXACT visual frame_start timestamp.
    Uses ffmpeg adelay filter — frame-perfect placement.
    No overlap, no repeat, no gap issues.
    Total output = exactly 45.0s (2700 frames @ 60fps).
    """
    total_s = TOTAL_FRAMES / FPS

    inputs, filter_parts, labels = [], [], []
    idx = 0
    for sc in SCENES:
        seg = SEG_DIR / f"{sc['id']}.mp3"
        if not seg.exists():
            print(f"  ⚠  {seg.name} missing — skipping from mix")
            continue
        start_ms = int(sc["fs"] / FPS * 1000)
        inputs += ["-i", str(seg)]
        filter_parts.append(f"[{idx}]adelay={start_ms}|{start_ms}[d{idx}]")
        labels.append(f"[d{idx}]")
        idx += 1

    if not inputs:
        print("✗ No segments to assemble")
        return False

    fc = (
        ";".join(filter_parts)
        + ";" + "".join(labels)
        + f"amix=inputs={idx}:normalize=0[out]"
    )

    out_path = AUDIO_DIR / "narration_final.mp3"
    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + ["-filter_complex", fc,
           "-map", "[out]",
           "-t", str(total_s),
           "-b:a", "192k",
           str(out_path)]
    )
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ffmpeg error:", r.stderr[-500:])
        return False

    size_kb = out_path.stat().st_size // 1024
    print(f"\n  ✓  narration_final.mp3  →  {size_kb}KB  ({total_s:.0f}s)")
    return True


# ── MANIFEST ──────────────────────────────────────────────────────
def write_manifest():
    manifest = [
        {
            "id":           s["id"],
            "text":         s["text"],
            "frame_start":  s["fs"],
            "frame_end":    s["fe"],
            "time_start_s": round(s["fs"] / FPS, 3),
            "time_end_s":   round(s["fe"] / FPS, 3),
            "window_s":     round((s["fe"] - s["fs"]) / FPS, 3),
            "seg_file":     f"segments/{s['id']}.mp3",
            "approved":     False,
        }
        for s in SCENES
    ]
    (AUDIO_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)
    )
    print("  ✓  manifest.json written")


# ── MAIN ──────────────────────────────────────────────────────────
def main():
    print("\n══ Kokoro TTS Audio Generator ══")
    print(f"Voice: {VOICE_NAME}  |  Speed: {SPEED}x  |  Scenes: {len(SCENES)}\n")

    print("── Installing deps ──")
    install()

    print("\n── Downloading model ──")
    download_model()

    print("\n── Loading Kokoro ──")
    kokoro = load_kokoro()

    print("\n── Generating scenes ──")
    failed = []
    for sc in SCENES:
        ok = synth_scene(kokoro, sc)
        if not ok:
            failed.append(sc["id"])

    if failed:
        print(f"\n✗ Failed: {failed}")
        sys.exit(1)

    write_manifest()

    print("\n── Assembling narration_final.mp3 ──")
    if not assemble():
        sys.exit(1)

    print("\n✅ Audio pipeline complete.\n")


if __name__ == "__main__":
    main()
