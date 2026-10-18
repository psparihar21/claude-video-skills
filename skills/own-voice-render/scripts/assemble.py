"""Timeline assembly, tempo fitting, loudness normalisation and encoding for own-voice-render."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit("ffmpeg failed:\n" + "\n".join((r.stderr or "").strip().splitlines()[-8:]))
    return r


def change_tempo(x: np.ndarray, sr: int, tempo: float, ffmpeg: str) -> np.ndarray:
    if abs(tempo - 1.0) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "in.wav", Path(d) / "out.wav"
        sf.write(a, x, sr, subtype="FLOAT")
        _run([ffmpeg, "-y", "-i", str(a), "-filter:a", f"atempo={tempo:.4f}", str(b)])
        return sf.read(b, dtype="float32")[0]


def fade_out(x: np.ndarray, sr: int, sec: float = 0.06) -> np.ndarray:
    n = min(len(x), int(sec * sr))
    if n > 0:
        x = x.copy()
        x[-n:] *= np.linspace(1.0, 0.0, n, dtype="float32")
    return x


def build_timeline(plan: dict, rendered: dict[str, np.ndarray], cfg: dict, ffmpeg: str, allow_overflow: bool):
    """Return (master, placements, issues). placements: id, start, end, window, tempo, status."""
    sr = cfg["sample_rate"]
    placements, issues = [], []
    segs: list[tuple[float, np.ndarray, dict]] = []
    if plan["mode"] == "timed":
        for c in plan["cues"]:
            x = rendered[c["id"]]
            window = c["out_sec"] - c["in_sec"]
            fit = core.plan_fit(len(x) / sr, window, cfg["tempo_cap"])
            st = fit["status"]
            if st in ("sped", "overflow"):
                x = change_tempo(x, sr, fit["tempo"], ffmpeg)
            if st == "overflow":
                if allow_overflow:
                    issues.append({"cue": c["id"], "level": "truncated",
                                   "msg": f"cut to fit its {window:.2f}s window (needed {fit['final']:.2f}s at max tempo): the end of the line is lost"})
                    x = fade_out(x[: int(max(window - 0.04, 0.3) * sr)], sr)
                else:
                    issues.append({"cue": c["id"], "level": "overflow",
                                   "msg": f"reads {fit['final']:.2f}s at max tempo {cfg['tempo_cap']} but the window is {window:.2f}s: shorten the line by ~{fit['over_by']:.2f}s"})
            segs.append((c["in_sec"], x, {"id": c["id"], "window": round(window, 3), "tempo": fit["tempo"], "status": st}))
        for (s0, x0, m0), (s1, _x1, m1) in zip(segs, segs[1:]):
            if s0 + len(x0) / sr > s1 + 0.02:
                issues.append({"cue": m0["id"], "level": "collision",
                               "msg": f"{m0['id']} ends at {s0 + len(x0) / sr:.2f}s, after {m1['id']} starts at {s1:.2f}s"})
    else:
        t = 0.0
        for i, c in enumerate(plan["cues"]):
            if i:
                t += cfg["gap_between_paragraphs_sec"] if c.get("paragraph_break") else cfg["gap_between_cues_sec"]
            x = rendered[c["id"]]
            segs.append((t, x, {"id": c["id"], "window": None, "tempo": 1.0, "status": "sequential"}))
            t += len(x) / sr
    total = max((s + len(x) / sr for s, x, _ in segs), default=0.0)
    if plan.get("video_duration_sec"):
        total = max(total, float(plan["video_duration_sec"]))
    master = np.zeros(int(round(total * sr)) + 1, dtype="float32")
    for s, x, meta in segs:
        i0 = int(round(s * sr))
        end = min(len(master), i0 + len(x))
        master[i0:end] += x[: end - i0]
        placements.append({**meta, "start": round(s, 3), "end": round(s + len(x) / sr, 3)})
    if plan.get("video_duration_sec"):
        master = master[: int(round(float(plan["video_duration_sec"]) * sr))]
    return master, placements, issues


def measure_loudness(wav: Path, ffmpeg: str, cfg: dict) -> dict:
    r = _run([ffmpeg, "-hide_banner", "-nostats", "-i", str(wav), "-af",
              f"loudnorm=I={cfg['target_lufs']}:TP={cfg['true_peak_db']}:LRA={cfg['loudness_range']}:print_format=json",
              "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        raise SystemExit("could not parse loudnorm output")
    return json.loads(m.group(0))


def normalise_and_encode(master: np.ndarray, out_dir: Path, cfg: dict, ffmpeg: str, name: str = "voice") -> dict:
    """Two-pass loudnorm (linear) to the target, 48 kHz mono 16-bit wav plus AAC m4a."""
    raw = out_dir / f"{name}.raw.wav"
    wav, m4a = out_dir / f"{name}.wav", out_dir / f"{name}.m4a"
    sf.write(raw, master, cfg["sample_rate"], subtype="FLOAT")
    live = float(np.sqrt((master ** 2).mean()))
    if live < 1e-5:
        raise SystemExit("rendered master is silent; nothing to normalise")
    meas = measure_loudness(raw, ffmpeg, cfg)
    sr = cfg["output_sample_rate"]
    af = (f"loudnorm=I={cfg['target_lufs']}:TP={cfg['true_peak_db']}:LRA={cfg['loudness_range']}:"
          f"measured_I={meas['input_i']}:measured_TP={meas['input_tp']}:measured_LRA={meas['input_lra']}:"
          f"measured_thresh={meas['input_thresh']}:offset={meas['target_offset']}:linear=true")
    _run([ffmpeg, "-y", "-i", str(raw), "-af", af, "-ar", str(sr), "-ac", "1", "-c:a", "pcm_s16le", str(wav)])
    _run([ffmpeg, "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "192k", str(m4a)])
    raw.unlink(missing_ok=True)
    final = measure_loudness(wav, ffmpeg, cfg)
    return {"wav": wav.name, "m4a": m4a.name, "input_lufs": float(meas["input_i"]), "input_tp": float(meas["input_tp"]),
            "output_lufs": float(final["input_i"]), "output_tp": float(final["input_tp"]),
            "duration_sec": round(len(master) / cfg["sample_rate"], 3), "sample_rate": sr}


def write_srt(plan: dict, placements: list[dict], path: Path) -> None:
    by_id = {c["id"]: c for c in plan["cues"]}
    lines = []
    for i, p in enumerate(placements, 1):
        text = by_id[p["id"]]["deva"] or by_id[p["id"]]["roman"]
        lines += [str(i), f"{core.fmt_srt_time(p['start'])} --> {core.fmt_srt_time(p['end'])}", text, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
