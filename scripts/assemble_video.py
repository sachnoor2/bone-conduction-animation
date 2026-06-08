#!/usr/bin/env python3
"""
assemble_video.py
─────────────────
Concatenates rendered chunk MP4s into one final 1080×1920 video.
Chunks must already be rendered by render-chunks.yml workflow.

Chunk overlap strategy:
  Each chunk has a 20-frame (0.333s) overlap baked into its render.
  We trim the last 20 frames from each chunk before concat to get
  seamless transitions (no duplicate frames).

Usage:
    python scripts/assemble_video.py
Input:
    out/chunk_01_hook.mp4
    out/chunk_02_setup.mp4
    ...
Output:
    out/BoneConduction_FINAL.mp4
"""

import subprocess, sys, json
from pathlib import Path

FPS       = 60
OVERLAP_F = 20                          # overlap frames baked into each chunk
OVERLAP_S = OVERLAP_F / FPS            # 0.333s
OUT_DIR   = Path("out")
OUT_DIR.mkdir(exist_ok=True)

CHUNKS = [
    "chunk_01_hook",
    "chunk_02_setup",
    "chunk_03_mechanism",
    "chunk_04_proof",
    "chunk_05_twist",
    "chunk_06_outro",
]


def run(cmd: list, check=True):
    print("  $", " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout: print(result.stdout[-500:])
    if result.stderr: print(result.stderr[-500:])
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.returncode}")
    return result


def get_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())


def trim_overlap(src: Path, dst: Path, is_last: bool):
    """
    Trim the overlap from the END of all chunks except the last.
    First chunk: no trim at start.
    """
    if is_last:
        # Last chunk: just copy
        run(["ffmpeg", "-y", "-i", str(src), "-c", "copy", str(dst)])
        return

    duration = get_duration(src)
    trimmed  = duration - OVERLAP_S
    run([
        "ffmpeg", "-y", "-i", str(src),
        "-t", str(trimmed),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        str(dst),
    ])


def concat(trimmed_files: list, output: Path):
    """Use FFmpeg concat demuxer for frame-perfect join."""
    list_file = OUT_DIR / "concat_list.txt"
    list_file.write_text(
        "\n".join(f"file '{f.resolve()}'" for f in trimmed_files)
    )
    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        str(output),
    ])


def main():
    print("\n── Bone Conduction — Video Assembler ──\n")

    # Verify all chunks present
    missing = []
    for c in CHUNKS:
        p = OUT_DIR / f"{c}.mp4"
        if not p.exists():
            missing.append(str(p))
    if missing:
        print("✗  Missing chunks:\n  " + "\n  ".join(missing))
        sys.exit(1)

    print("▶  All chunks found. Trimming overlaps...\n")

    trimmed = []
    for i, chunk_id in enumerate(CHUNKS):
        src = OUT_DIR / f"{chunk_id}.mp4"
        dst = OUT_DIR / f"{chunk_id}_trimmed.mp4"
        is_last = (i == len(CHUNKS) - 1)
        print(f"  [{i+1}/{len(CHUNKS)}] {chunk_id} → {dst.name}")
        trim_overlap(src, dst, is_last)
        trimmed.append(dst)

    print("\n▶  Concatenating into final video...\n")
    final = OUT_DIR / "BoneConduction_FINAL.mp4"
    concat(trimmed, final)

    dur = get_duration(final)
    size_mb = final.stat().st_size / 1024 / 1024
    print(f"\n✅  Final video: {final}")
    print(f"    Duration : {dur:.2f}s")
    print(f"    Size     : {size_mb:.1f} MB")
    print(f"    Format   : 1080×1920 @{FPS}fps\n")

    # Write build metadata
    meta = {
        "output": str(final),
        "duration_s": round(dur, 2),
        "size_mb": round(size_mb, 1),
        "chunks": CHUNKS,
    }
    (OUT_DIR / "build_meta.json").write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
