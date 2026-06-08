#!/usr/bin/env python3
"""
check_audio_sync.py  —  AI Audio-Visual Sync Checker + Auto Re-renderer
────────────────────────────────────────────────────────────────────────
Reads public/audio/manifest.json (written by generate_audio.py).

For each scene:
  1. Measures actual audio duration via ffprobe
  2. Compares to visual window (frame_end - frame_start) @ 60fps
  3. Classifies: PASS / TRIM / SLOW / MISSING
  4. TRIM  → hard-trim with ffmpeg (small overshoot ≤1.5s)
  5. SLOW  → re-render with Kokoro at higher speed until it fits
  6. MISSING → full re-render
  7. Rebuilds narration_final.mp3 if anything changed

Designed to be small, fast, and robust — zero ML inference except
for re-renders that actually need it.
"""

import sys, json, math, subprocess
from pathlib import Path

FPS          = 60
TOLERANCE_S  = 0.28          # ±280ms is acceptable
VOICE_NAME   = "am_fenrir"
SPEED_BASE   = 1.08
LANG         = "hi"
MODEL_PATH   = Path("/tmp/kokoro-v1.0.onnx")
VOICES_PATH  = Path("/tmp/voices-v1.0.bin")
MANIFEST     = Path("public/audio/manifest.json")
SEG_DIR      = Path("public/audio/segments")
REPORT_PATH  = Path("public/audio/sync_report.json")
TOTAL_FRAMES = 2700
MAX_RERENDERS = 3


# ── UTILS ────────────────────────────────────────────────────────

def duration_s(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def trim_audio(src: Path, max_s: float) -> bool:
    tmp = src.with_suffix(".trim.mp3")
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-t", str(max_s),
         "-acodec", "libmp3lame", "-b:a", "192k", str(tmp)],
        capture_output=True
    )
    if r.returncode == 0:
        tmp.replace(src)
        return True
    return False


def load_kokoro():
    from kokoro_onnx import Kokoro
    return Kokoro(str(MODEL_PATH), str(VOICES_PATH))


def rerender(kokoro, scene: dict, speed: float, out: Path) -> bool:
    import soundfile as sf
    from pydub import AudioSegment

    try:
        samples, sr = kokoro.create(
            scene["text"], voice=VOICE_NAME,
            speed=speed, lang=LANG,
        )
        wav = out.with_suffix(".wav")
        sf.write(str(wav), samples, sr)
        seg = AudioSegment.from_wav(str(wav))
        seg.export(str(out), format="mp3", bitrate="192k")
        wav.unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"    rerender error: {e}")
        return False


# ── SCENE CHECK ───────────────────────────────────────────────────

def check_scene(scene: dict) -> dict:
    seg  = SEG_DIR / scene["seg_file"].split("/")[-1]
    win  = scene["window_s"]

    if not seg.exists() or seg.stat().st_size < 1000:
        return {"status": "MISSING", "audio_s": 0.0, "window_s": win, "delta_s": win}

    dur  = duration_s(seg)
    delta = dur - win

    if delta <= TOLERANCE_S:
        status = "PASS"
    elif delta <= 1.5:
        status = "TRIM"
    else:
        status = "SLOW"

    return {"status": status, "audio_s": round(dur, 3),
            "window_s": round(win, 3), "delta_s": round(delta, 3)}


def fix_scene(kokoro, scene: dict, result: dict) -> bool:
    seg  = SEG_DIR / scene["seg_file"].split("/")[-1]
    win  = result["window_s"]

    if result["status"] == "TRIM":
        print(f"    ✂  trimming to {win + TOLERANCE_S * 0.5:.2f}s")
        return trim_audio(seg, win + TOLERANCE_S * 0.5)

    # SLOW or MISSING — re-render at higher speed
    audio_s = result["audio_s"] if result["audio_s"] > 0 else win * 1.5
    speed   = min(1.65, SPEED_BASE * (audio_s / max(win - 0.1, 0.1)))

    for attempt in range(1, MAX_RERENDERS + 1):
        print(f"    ⚡  re-render attempt {attempt}  speed={speed:.2f}x")
        ok = rerender(kokoro, scene, speed, seg)
        if not ok:
            speed = min(1.65, speed * 1.1)
            continue
        new_dur = duration_s(seg)
        print(f"       result: {new_dur:.2f}s  (window={win:.2f}s)")
        if new_dur <= win + TOLERANCE_S:
            return True
        speed = min(1.65, speed * 1.12)

    # Last resort: trim whatever we got
    print(f"    ✂  last-resort trim")
    return trim_audio(seg, win + TOLERANCE_S * 0.5)


# ── REASSEMBLE ───────────────────────────────────────────────────

def assemble(manifest: list):
    from pydub import AudioSegment

    total_s  = TOTAL_FRAMES / FPS
    total_ms = int(total_s * 1000)
    timeline = AudioSegment.silent(duration=total_ms, frame_rate=44100)

    for sc in manifest:
        seg = SEG_DIR / sc["seg_file"].split("/")[-1]
        if not seg.exists():
            continue
        audio    = AudioSegment.from_mp3(str(seg))
        start_ms = int(sc["time_start_s"] * 1000)
        timeline = timeline.overlay(audio, position=start_ms)

    out = Path("public/audio/narration_final.mp3")
    timeline.export(str(out), format="mp3", bitrate="192k")
    print(f"  ✓  narration_final.mp3 rebuilt  ({out.stat().st_size//1024}KB)")


# ── MAIN ─────────────────────────────────────────────────────────

def main():
    if not MANIFEST.exists():
        print("✗  manifest.json not found — run generate_audio.py first")
        sys.exit(1)

    manifest = json.loads(MANIFEST.read_text())
    report   = []
    needs_reassemble = False
    kokoro   = None   # lazy-load only if re-renders needed

    print("\n══ Audio-Visual Sync Check ══\n")
    ICONS = {"PASS": "✅", "TRIM": "✂ ", "SLOW": "⚡", "MISSING": "❌", "APPROVED": "✅"}

    for scene in manifest:
        if scene.get("approved"):
            print(f"  ✅  {scene['id']}  already approved")
            report.append({**scene, "check": {"status": "APPROVED"}})
            continue

        result = check_scene(scene)
        icon   = ICONS.get(result["status"], "?")
        print(
            f"  {icon}  {scene['id']}:  {result['status']:<8}"
            f"  audio={result['audio_s']:.2f}s"
            f"  window={result['window_s']:.2f}s"
            f"  delta={result['delta_s']:+.2f}s"
        )

        if result["status"] == "PASS":
            scene["approved"] = True
        else:
            # Lazy-load Kokoro model only when first re-render needed
            if kokoro is None and result["status"] in ("SLOW", "MISSING"):
                print("  → loading Kokoro model for re-render...")
                kokoro = load_kokoro()

            fixed = fix_scene(kokoro, scene, result)
            if fixed:
                recheck = check_scene(scene)
                print(f"       after fix: {recheck['status']}  audio={recheck['audio_s']:.2f}s")
                scene["approved"] = (recheck["status"] == "PASS")
            else:
                print(f"       ⚠  could not fix {scene['id']}")
                scene["approved"] = False

            needs_reassemble = True

        report.append({**scene, "check": result})

    # Save updated manifest + report
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n  ✓  sync_report.json saved")

    if needs_reassemble:
        print("\n── Rebuilding narration_final.mp3 ──")
        assemble(manifest)

    unapproved = [s["id"] for s in manifest if not s.get("approved")]
    if unapproved:
        print(f"\n⚠  Unapproved after all fixes: {unapproved}")
        sys.exit(1)

    print("\n✅  All scenes approved — sync check passed.\n")


if __name__ == "__main__":
    main()
