"""GPU Whisper (faster-whisper large-v3) for Hindi / Hinglish, word timestamps.

Writes the same shape as Parakeet (`[{id,text,start,end}]`) so the rest of the
pipeline does not care which engine ran, plus a vtc-format copy for
video-timeline-copilot.

Usage (run with the vtc tool's Python, which has faster-whisper + CUDA libs):
  & "$env:APPDATA\\uv\\tools\\video-timeline-copilot\\Scripts\\python.exe" -I whisper_gpu.py INPUT OUT_DIR [--language hi|en|auto] [--model large-v3] [--prompt "Claude Code, DaVinci Resolve"]
"""
import argparse
import json
import os
import site
import subprocess
import sys
from pathlib import Path


def add_cuda_dlls() -> None:
    # pip-installed nvidia-cublas-cu12 / nvidia-cudnn-cu12 ship DLLs that are not on PATH.
    for base in site.getsitepackages():
        nv = Path(base) / "nvidia"
        if not nv.is_dir():
            continue
        for bin_dir in nv.glob("*/bin"):
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("out_dir", type=Path)
    p.add_argument("--language", default="hi", help="hi, en, or auto")
    p.add_argument("--model", default="large-v3")
    p.add_argument("--device", default="cuda")
    p.add_argument("--prompt", default=None, help="Names to spell right, e.g. 'Claude Code, DaVinci Resolve, Valorant'")
    args = p.parse_args()

    add_cuda_dlls()
    import numpy as np
    from faster_whisper import WhisperModel

    # Decode with FFmpeg (GPU-decoded when possible) instead of faster-whisper's
    # PyAV path, which breaks on newer PyAV releases.
    pcm = subprocess.run(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(args.input),
         "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
        check=True, capture_output=True,
    ).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)

    compute = "float16" if args.device == "cuda" else "int8"
    model = WhisperModel(args.model, device=args.device, compute_type=compute)
    lang = None if args.language == "auto" else args.language
    segments, info = model.transcribe(
        audio,
        language=lang,
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=False,
        initial_prompt=args.prompt,
        hotwords=args.prompt,
    )

    words, segs = [], []
    for seg in segments:
        seg_words = []
        for w in seg.words or []:
            item = {"start": round(w.start, 3), "end": round(w.end, 3), "text": w.word.strip(), "probability": round(w.probability, 3)}
            seg_words.append(item)
            words.append({"id": f"w{len(words)}", "text": item["text"], "start": item["start"], "end": item["end"]})
        segs.append({"start": seg.start, "end": seg.end, "text": seg.text.strip(), "words": seg_words})

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "transcript.json").write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")
    vtc = {
        "source": str(args.input.resolve()),
        "language": info.language,
        "language_probability": info.language_probability,
        "duration": info.duration,
        "engine": f"faster-whisper {args.model} ({args.device})",
        "segments": segs,
        "words": [w for s in segs for w in s["words"]],
    }
    (args.out_dir / "transcript.vtc.json").write_text(json.dumps(vtc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "engine": vtc["engine"], "language": info.language,
                      "language_probability": round(info.language_probability, 3),
                      "wordCount": len(words), "durationSeconds": round(info.duration, 2)}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
