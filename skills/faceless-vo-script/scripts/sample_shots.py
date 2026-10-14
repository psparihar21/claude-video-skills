#!/usr/bin/env python3
"""Pull one frame per shot so the voiceover pass can see the locked edit.

Requires ffmpeg. Frames land in the output directory next to manifest.json.
This does not interpret the picture. The agent looks at the frames.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if not found:
        raise SystemExit("ffmpeg is not on PATH. Install it, or write from the shot notes and mark confidence low.")
    return found


def resolve_video(edit_path: Path, edit: dict) -> Path:
    raw = edit.get("video_path") or ""
    if not raw:
        raise SystemExit("edit.json has no video_path. Nothing to sample.")
    path = Path(raw)
    if not path.is_absolute():
        path = (edit_path.parent / path).resolve()
    if not path.exists():
        raise SystemExit(f"video not found: {path}")
    return path


def midpoint(shot: dict) -> float:
    start = float(shot["in_sec"])
    end = float(shot["out_sec"])
    if end - start < 0.2:
        return start + 0.05
    return start + (end - start) / 2


def grab(video: Path, at: float, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg(), "-y",
        "-ss", f"{at:.3f}",
        "-i", str(video),
        "-frames:v", "1",
        "-vf", "scale=640:-1",
        "-q:v", "4",
        str(dest),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        tail = (result.stderr or "").strip().splitlines()[-4:]
        raise SystemExit(f"ffmpeg failed for {dest.name} at {at:.3f}s\n" + "\n".join(tail))


def sample(edit_path: Path, out_dir: Path, only: set[str] | None) -> dict:
    edit = load(edit_path)
    video = resolve_video(edit_path, edit)
    frames = []
    for shot in edit["shots"]:
        if only and shot["id"] not in only:
            continue
        at = midpoint(shot)
        dest = out_dir / f"{shot['id']}.jpg"
        grab(video, at, dest)
        frames.append({
            "shot_id": shot["id"],
            "at_sec": round(at, 3),
            "file": dest.name,
            "visual": shot.get("visual", ""),
        })
    manifest = {"video": str(video), "frames": frames}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        video = root / "color.mp4"
        command = [
            ffmpeg(), "-y",
            "-f", "lavfi", "-i", "color=c=black:s=320x180:d=2",
            "-pix_fmt", "yuv420p",
            str(video),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stderr)
            return 1
        edit_path = root / "edit.json"
        edit_path.write_text(json.dumps({
            "title": "probe",
            "video_path": video.name,
            "shots": [
                {
                    "id": "s01",
                    "in_sec": 0,
                    "out_sec": 2,
                    "visual": "black",
                    "energy": "hook",
                    "cut_type": "hard",
                }
            ],
        }), encoding="utf-8")
        manifest = sample(edit_path, root / "frames", None)
        frame = root / "frames" / manifest["frames"][0]["file"]
        if not frame.exists() or frame.stat().st_size < 100:
            print("frame missing")
            return 1
        print(f"ok sample_shots {frame.stat().st_size} bytes")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample one frame at the midpoint of each shot.")
    parser.add_argument("--edit", type=Path, help="Path to edit.json")
    parser.add_argument("--out", type=Path, help="Directory for jpg frames and manifest.json")
    parser.add_argument("--ids", type=str, default="", help="Comma-separated shot ids to sample")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.edit or not args.out:
        parser.error("provide --edit and --out, or --self-test")
    only = {item.strip() for item in args.ids.split(",") if item.strip()} or None
    manifest = sample(args.edit, args.out, only)
    print(f"{len(manifest['frames'])} frame(s) in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
