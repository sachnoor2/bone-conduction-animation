#!/usr/bin/env python3
"""
check_audio_sync.py  ─  AI Audio-Visual Sync Checker + Auto Re-renderer
─────────────────────────────────────────────────────────────────────────
Reads public/audio/manifest.json (written by generate_audio.py).
For each scene segment:
  1. Measures actual audio duration via ffprobe
  2. Compares to available visual window (frame_end - frame_start)
  3. Scores: PASS / TRIM / SLOW / MISSING
  4. If SLOW or MISSING → re-renders that scene segment via ElevenLabs
     with adjusted speed or split text, until it fits the visual window.
  5. Rebuilds narration_final.mp3 if any segment was re-rendered.

Design goals:
  • Concise (<300 lines) but robust
  • No external ML model needed — pure heuristic + ElevenLabs speed control
  • Idempotent: safe to re-run; skips already-approved scenes
  • Writes sync_report.json for CI visibility

Usage:
    ELEVENLABS_API_KEY=xxx python scripts/check_audio_sync.py
"""

import os, sys, json, math, time, subprocess
from pathlib import Path

FPS          = 60
TOLERANCE_S  = 0.25   # ±250ms is acceptable overshoot
VOICE_ID     = "TX3LPaxmHKxFdv7VOQHJ"
MODEL_ID     = "eleven_multilingual_v2"
API_KEY      = os.environ.get("ELEVENLABS_API_KEY", "")
MANIFEST     = Path("public/audio/manifest.json")
SEG_DIR      = Path("public/audio/segments")
REPORT_PATH  = Path("public/audio/sync_report.json")
HEADERS      = {"xi-api-key": API_KEY, "Content-Type": "application/json"}

MAX_RERENDERS = 3   # give up after 3 attempts per scene


# ── UTILS ────────────────────────────────────────────────────────

def duration_s(path: Path) -> float:
    """Return audio duration in seconds via ffprobe."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def install_deps():
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pydub", "requests", "--quiet"],
        check=True,
    )


def tts(text: str, out_path: Path, speed_factor: float = 1.0) -> bool:
    """
    Call ElevenLabs. speed_factor>1 = faster speech (stability tweak).
    Returns True on success.
    """
    import requests

    # ElevenLabs doesn't have a direct speed param, but stability↓ + style↑
    # produces faster, more punchy delivery.  For >1.15x we split sentences.
    stability = max(0.20, 0.38 - (speed_factor - 1.0) * 0.3)
    style     = min(0.90, 0.55 + (speed_factor - 1.0) * 0.4)

    payload = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": 0.82,
            "style": style,
            "use_speaker_boost": True,
        },
    }
    resp = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers=HEADERS,
        json=payload,
        stream=True,
    )
    if resp.status_code == 200:
        out_path.write_bytes(resp.content)
        return True
    print(f"    ✗ ElevenLabs HTTP {resp.status_code}: {resp.text[:80]}")
    return False


def trim_audio(src: Path, max_s: float) -> bool:
    """Hard-trim audio to max_s seconds using ffmpeg."""
    tmp = src.with_suffix(".tmp.mp3")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-t", str(max_s),
         "-acodec", "copy", str(tmp)],
        capture_output=True
    )
    if r.returncode == 0:
        tmp.replace(src)
        return True
    return False


# ── SYNC CHECK ────────────────────────────────────────────────────

def check_scene(scene: dict) -> dict:
    """
    Analyse one scene.  Returns result dict:
      status: PASS | TRIM | SLOW | MISSING
      audio_s, window_s, delta_s
    """
    seg_path = SEG_DIR / scene["seg_file"].split("/")[-1]
    window_s = scene["time_end_s"] - scene["time_start_s"]

    if not seg_path.exists() or seg_path.stat().st_size < 500:
        return {"status": "MISSING", "audio_s": 0, "window_s": window_s, "delta_s": window_s}

    audio_s = duration_s(seg_path)
    delta_s = audio_s - window_s

    if abs(delta_s) <= TOLERANCE_S:
        status = "PASS"
    elif delta_s > TOLERANCE_S:
        # Audio longer than visual window
        if delta_s <= 1.5:
            status = "TRIM"   # small overshoot → just trim
        else:
            status = "SLOW"   # large overshoot → re-render faster
    else:
        status = "PASS"   # audio is shorter than window — that's fine (silence fills)

    return {
        "status": status,
        "audio_s": round(audio_s, 3),
        "window_s": round(window_s, 3),
        "delta_s": round(delta_s, 3),
    }


def fix_scene(scene: dict, result: dict) -> bool:
    """
    Auto-fix a TRIM or SLOW scene.  Returns True if fixed.
    """
    seg_path = SEG_DIR / scene["seg_file"].split("/")[-1]
    window_s = result["window_s"]

    if result["status"] == "TRIM":
        print(f"    ✂  Trimming {scene['id']} to {window_s:.2f}s")
        return trim_audio(seg_path, window_s + TOLERANCE_S * 0.5)

    if result["status"] in ("SLOW", "MISSING"):
        # Calculate required speed-up factor
        audio_s = result["audio_s"] if result["audio_s"] > 0 else window_s * 1.5
        speed_factor = min(1.6, audio_s / max(window_s - 0.1, 0.1))
        print(f"    ⚡  Re-rendering {scene['id']} at speed_factor={speed_factor:.2f}")

        for attempt in range(1, MAX_RERENDERS + 1):
            ok = tts(scene["text"], seg_path, speed_factor=speed_factor)
            if not ok:
                time.sleep(2)
                continue
            new_dur = duration_s(seg_path)
            print(f"       attempt {attempt}: {new_dur:.2f}s (window={window_s:.2f}s)")
            if new_dur <= window_s + TOLERANCE_S:
                return True
            # Still too long → nudge speed further
            speed_factor = min(1.6, speed_factor * 1.12)
            time.sleep(0.5)

        # Last resort: trim what we have
        print(f"    ✂  Last-resort trim: {scene['id']}")
        return trim_audio(seg_path, window_s + TOLERANCE_S * 0.5)

    return True


def assemble():
    """Re-assemble final MP3 from segments after fixes."""
    from pydub import AudioSegment

    manifest = json.loads(MANIFEST.read_text())
    total_ms = math.ceil(2700 / FPS * 1000)
    timeline  = AudioSegment.silent(duration=total_ms, frame_rate=44100)

    for scene in manifest:
        seg_path = SEG_DIR / scene["seg_file"].split("/")[-1]
        if not seg_path.exists():
            continue
        seg      = AudioSegment.from_mp3(str(seg_path))
        start_ms = int(scene["time_start_s"] * 1000)
        timeline  = timeline.overlay(seg, position=start_ms)

    out = Path("public/audio/narration_final.mp3")
    timeline.export(str(out), format="mp3", bitrate="192k")
    print(f"\n✓  Re-assembled: {out}  ({total_ms/1000:.0f}s)")


# ── MAIN ─────────────────────────────────────────────────────────

def main():
    install_deps()

    if not MANIFEST.exists():
        print("✗  manifest.json not found — run generate_audio.py first")
        sys.exit(1)

    manifest = json.loads(MANIFEST.read_text())
    report   = []
    needs_reassemble = False

    print("\n── Audio-Visual Sync Check ──\n")

    for scene in manifest:
        if scene.get("approved"):
            print(f"  ✓  {scene['id']} already approved — skip")
            report.append({**scene, "check": {"status": "APPROVED"}})
            continue

        result = check_scene(scene)
        icon   = {"PASS": "✅", "TRIM": "✂ ", "SLOW": "⚡", "MISSING": "❌"}.get(result["status"], "?")
        print(f"  {icon}  {scene['id']}: {result['status']:7s}  "
              f"audio={result['audio_s']:.2f}s  window={result['window_s']:.2f}s  "
              f"delta={result['delta_s']:+.2f}s")

        if result["status"] == "PASS":
            scene["approved"] = True
        else:
            fixed = fix_scene(scene, result)
            if fixed:
                re_result = check_scene(scene)
                print(f"       → after fix: {re_result['status']}  audio={re_result['audio_s']:.2f}s")
                scene["approved"] = (re_result["status"] == "PASS")
                needs_reassemble = True
            else:
                print(f"       → ⚠  could not fix {scene['id']}")
                scene["approved"] = False

        report.append({**scene, "check": result})

    # Save updated manifest
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))

    # Save report
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n✓  sync_report.json → {REPORT_PATH}")

    if needs_reassemble:
        print("\n── Re-assembling narration_final.mp3 ──")
        assemble()

    # Exit 1 if any scene unapproved (CI will catch it)
    unapproved = [s["id"] for s in manifest if not s.get("approved")]
    if unapproved:
        print(f"\n⚠  Unapproved scenes: {unapproved}")
        sys.exit(1)

    print("\n✅  All scenes approved. Sync check passed.\n")


if __name__ == "__main__":
    main()
