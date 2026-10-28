#!/usr/bin/env python3
"""Measure a reference video for craft study: shots, cut rhythm, speech pace, loudness, hook, contact sheets.

Usage:
    python3 analyze_reference.py VIDEO PRODUCTION_DIR [--scene 0.30] [--language auto|hi|en]
                                 [--whisper-model large-v3] [--no-transcribe]

Needs ffmpeg and ffprobe on PATH. Transcribes with faster-whisper when the interpreter has it;
otherwise keeps an existing reference/transcript.txt or asks for one.

Writes PRODUCTION_DIR/reference/:
    analysis.md        human summary to read first
    metrics.json       every number below, machine-readable
    shots.csv          shot start, end, length
    transcript.txt     plain text (what similarity_guard.py compares against)
    transcript.json    segments with timestamps
    sheets/sheet_NN.jpg   one labelled frame per shot, 4x4 per sheet
    hook/hook_sheet.jpg   one frame per second for the first 15 s

Everything here is study material. check_package.py fails any shot or rights row that points into reference/.
"""
import argparse
import csv
import glob
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BUCKET = 30.0      # seconds per pacing bucket
HOOK = 15          # seconds of hook to sample
MAX_SHEET_SHOTS = 64


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def probe(video):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", video])
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    num, den = (v.get("avg_frame_rate", "0/1").split("/") + ["1"])[:2]
    return {
        "duration_s": round(float(d["format"]["duration"]), 2),
        "width": v.get("width"), "height": v.get("height"),
        "fps": round(float(num) / float(den), 2) if float(den) else None,
        "has_audio": a is not None,
    }


def detect_cuts(video, threshold):
    r = run(["ffmpeg", "-hide_banner", "-i", video, "-an", "-vf",
             f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-f", "null", "-"])
    return [round(float(t), 2) for t in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def long_path(path):
    """Windows refuses paths over 260 characters unless they carry the long-path prefix; ffmpeg accepts it."""
    p = os.path.abspath(path)
    if os.name == "nt" and len(p) >= 200 and not p.startswith(chr(92) * 2 + "?"):
        p = chr(92) * 2 + "?" + chr(92) + p
    return p


def font_path():
    for p in ("C:/Windows/Fonts/arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf"):
        if os.path.exists(p):
            return p
    return None


def grab(video, t, out, label, font):
    vf = "scale=320:-2"
    if font:
        f = font.replace(":", "\\:")
        vf += (f",drawtext=fontfile='{f}':text='{label}':x=6:y=6:fontsize=18:"
               "fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=4")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-vf", vf, "-q:v", "4", out])


def tile(frames_dir, pattern, out_pattern, cols=4, rows=4):
    run(["ffmpeg", "-v", "error", "-y", "-framerate", "1", "-i", os.path.join(frames_dir, pattern),
         "-vf", f"tile={cols}x{rows}:padding=4:color=black", "-q:v", "4", "-f", "image2", out_pattern])


def loudness(video):
    r = run(["ffmpeg", "-hide_banner", "-i", video, "-vn", "-af", "ebur128=framelog=quiet", "-f", "null", "-"])
    i = re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
    lra = re.findall(r"LRA:\s+([0-9.]+) LU", r.stderr)
    return (float(i[-1]) if i else None), (float(lra[-1]) if lra else None)


def silences(video, noise="-35dB", dur=0.4):
    r = run(["ffmpeg", "-hide_banner", "-i", video, "-vn", "-af", f"silencedetect=noise={noise}:d={dur}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", r.stderr)]
    lens = [float(x) for x in re.findall(r"silence_duration: ([0-9.]+)", r.stderr)]
    return list(zip(starts, lens))


def transcribe(video, model_name, language):
    try:
        import numpy as np
        if os.name == "nt":  # CUDA DLLs shipped as pip wheels are not on the search path by default
            import site
            for sp in site.getsitepackages():
                for d in glob.glob(os.path.join(sp, "nvidia", "*", "bin")):
                    os.add_dll_directory(d)
                    os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]
        from faster_whisper import WhisperModel
    except Exception as e:
        return None, f"faster-whisper not available in this interpreter ({e.__class__.__name__})"
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", video, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    audio = np.frombuffer(raw, np.float32)
    for device, ctype in (("cuda", "float16"), ("cpu", "int8")):
        try:
            m = WhisperModel(model_name, device=device, compute_type=ctype)
            segs, info = m.transcribe(audio, language=None if language == "auto" else language, vad_filter=True)
            segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
            return {"language": info.language, "segments": segs, "device": device}, None
        except Exception as e:
            err = f"{device}: {e}"
    return None, f"transcription failed ({err})"


def buckets(duration, events):
    n = max(1, int(duration // BUCKET) + (1 if duration % BUCKET else 0))
    out = [0] * n
    for t in events:
        out[min(n - 1, int(t // BUCKET))] += 1
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("production_dir")
    ap.add_argument("--scene", type=float, default=0.30, help="scene-change threshold (lower = more cuts)")
    ap.add_argument("--language", default="auto")
    ap.add_argument("--whisper-model", default="large-v3")
    ap.add_argument("--no-transcribe", action="store_true")
    a = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"FAIL: {tool} not on PATH")
            return 2
    a.video, a.production_dir = long_path(a.video), long_path(a.production_dir)
    if not os.path.isfile(a.video):
        print(f"FAIL: video not found: {a.video}")
        return 2

    ref = Path(a.production_dir) / "reference"
    sheets, hook, frames = ref / "sheets", ref / "hook", ref / "_frames"
    for d in (sheets, hook, frames):
        d.mkdir(parents=True, exist_ok=True)
    font = font_path()

    info = probe(a.video)
    dur = info["duration_s"]
    print(f"probe: {dur}s {info['width']}x{info['height']} {info['fps']}fps audio={info['has_audio']}", flush=True)

    # shots
    cuts = [c for c in detect_cuts(a.video, a.scene) if 0.2 < c < dur - 0.2]
    bounds = [0.0] + cuts + [dur]
    shots = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
    lens = [round(e - s, 2) for s, e in shots]
    with open(ref / "shots.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["shot", "start_s", "end_s", "length_s"])
        for i, ((s, e), L) in enumerate(zip(shots, lens), 1):
            w.writerow([i, f"{s:.2f}", f"{e:.2f}", f"{L:.2f}"])
    cut_buckets = buckets(dur, cuts)
    print(f"shots: {len(shots)}, avg {statistics.mean(lens):.2f}s", flush=True)

    # contact sheets: one mid-shot frame per shot (evenly sampled if very many)
    for old in frames.glob("*.jpg"):
        os.remove(old)
    step = max(1, len(shots) // MAX_SHEET_SHOTS + (1 if len(shots) % MAX_SHEET_SHOTS else 0))
    picked = list(enumerate(shots, 1))[::step]
    for k, (i, (s, e)) in enumerate(picked):
        t = (s + e) / 2
        grab(a.video, t, str(frames / f"s_{k:04d}.jpg"), f"#{i}  {t:.1f}s", font)
    tile(str(frames), "s_%04d.jpg", str(sheets / "sheet_%02d.jpg"))
    for k in range(min(HOOK, int(dur))):
        grab(a.video, k + 0.5, str(frames / f"h_{k:04d}.jpg"), f"{k}s", font)
    tile(str(frames), "h_%04d.jpg", str(hook / "hook_sheet.jpg"), cols=5, rows=3)
    shutil.rmtree(frames, ignore_errors=True)

    # audio
    lufs = lra = None
    sil = []
    if info["has_audio"]:
        lufs, lra = loudness(a.video)
        sil = silences(a.video)
    long_pauses = [(round(s, 1), round(L, 1)) for s, L in sil if L >= 1.0]

    # transcript
    tr, note = (None, "skipped (--no-transcribe)") if a.no_transcribe else (None, None)
    if not a.no_transcribe and info["has_audio"]:
        tr, note = transcribe(a.video, a.whisper_model, a.language)
    words_total, wpm, wpm_buckets, hook_text, questions = None, None, [], "", None
    if tr:
        segs = tr["segments"]
        (ref / "transcript.json").write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding="utf-8")
        (ref / "transcript.txt").write_text("\n".join(s["text"] for s in segs), encoding="utf-8")
        words_total = sum(len(s["text"].split()) for s in segs)
        wpm = round(words_total / (dur / 60), 1)
        per = [0] * len(cut_buckets)
        for s in segs:
            per[min(len(per) - 1, int(s["start"] // BUCKET))] += len(s["text"].split())
        spans = [min(BUCKET, dur - i * BUCKET) for i in range(len(per))]
        wpm_buckets = [round(c * 60 / sp, 0) if sp > 0 else 0 for c, sp in zip(per, spans)]
        hook_text = " ".join(s["text"] for s in segs if s["start"] < HOOK)
        questions = sum(s["text"].count("?") for s in segs)
    elif (ref / "transcript.txt").exists():
        note = (note or "") + "; using existing reference/transcript.txt"

    metrics = {
        "video": os.path.basename(a.video), **info,
        "shots": len(shots), "cuts_per_min": round(len(cuts) / (dur / 60), 1),
        "avg_shot_s": round(statistics.mean(lens), 2), "median_shot_s": round(statistics.median(lens), 2),
        "longest_shot_s": max(lens), "shots_over_8s": sum(L > 8 for L in lens),
        "cuts_per_30s": cut_buckets, "scene_threshold": a.scene,
        "integrated_lufs": lufs, "loudness_range_lu": lra,
        "pauses_over_1s": long_pauses,
        "transcript": {"language": tr["language"] if tr else None, "words": words_total, "wpm": wpm,
                       "wpm_per_30s": wpm_buckets, "questions": questions, "note": note},
        "hook_first_15s": hook_text,
        "sheets": sorted(os.path.relpath(str(p), a.production_dir) for p in sheets.glob("*.jpg")),
        "hook_sheet": os.path.relpath(str(hook / "hook_sheet.jpg"), a.production_dir),
    }
    (ref / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=1), encoding="utf-8")

    def fmt_buckets(vals):
        return " | ".join(f"{int(i * BUCKET // 60)}:{int(i * BUCKET % 60):02d} {v:g}" for i, v in enumerate(vals))

    md = [
        f"# Reference analysis: {metrics['video']}",
        "",
        "Study material only. Nothing in this folder may appear in the new video.",
        "",
        "| Measure | Value |", "|---|---|",
        f"| Length | {dur:.0f} s ({dur / 60:.1f} min), {info['width']}x{info['height']}, {info['fps']} fps |",
        f"| Shots | {len(shots)} ({metrics['cuts_per_min']} cuts/min) |",
        f"| Shot length | avg {metrics['avg_shot_s']} s, median {metrics['median_shot_s']} s, longest {metrics['longest_shot_s']} s, {metrics['shots_over_8s']} shots over 8 s |",
        f"| Speech pace | {wpm if wpm else 'n/a'} wpm ({words_total or 'n/a'} words, language {metrics['transcript']['language'] or 'n/a'}) |",
        f"| Loudness | {lufs if lufs is not None else 'n/a'} LUFS integrated, LRA {lra if lra is not None else 'n/a'} LU |",
        f"| Pauses over 1 s | {len(long_pauses)} {long_pauses[:8]} |",
        f"| Questions asked | {questions if questions is not None else 'n/a'} |",
        "",
        f"**Cuts per 30 s:** {fmt_buckets(cut_buckets)}",
        "",
        f"**Words per minute per 30 s:** {fmt_buckets(wpm_buckets) if wpm_buckets else 'n/a'}",
        "",
        f"**First {HOOK} s (spoken):** {hook_text or 'n/a'}",
        "",
        f"Transcript note: {note or 'ok'}",
        "",
        "Look at next: " + ", ".join([metrics["hook_sheet"]] + metrics["sheets"]),
    ]
    (ref / "analysis.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {ref / 'analysis.md'}")
    print(f"transcript: {note or 'ok'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
