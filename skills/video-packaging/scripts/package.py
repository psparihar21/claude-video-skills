# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10", "numpy>=1.24"]
# ///
"""video-packaging renderer.

  analyze <video> --out DIR     one low-res decode pass -> ranked, de-duplicated candidates,
                                candidates.jpg, contact_sheet.jpg, audio measurement, analysis.json
  render  <brief.json>          one cover JPEG from one real frame: subject-aware crop, light grade,
                                scrim, type; hard checks + <out>.preview.jpg
  check   <cover.jpg> --platform P
                                verify any export (e.g. from Canva) and write a preview sheet

Never re-encodes or modifies the source video. Never generates imagery.
Exit codes: 0 ok, 2 brief refused, 3 export check failed, 1 other error.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

SKILL_DIR = Path(__file__).resolve().parent.parent
MAX_BYTES = 2 * 1024 * 1024

# Keep in sync with references/platforms.md.
#   box     where type may sit, per side (x0, y0, x1, y1 as fractions of W/H)
#   forbid  zones type must never touch
#   tiny    smallest real display width in px (phone feed/grid) used for the read test
#   budget  max share of the canvas the text block may cover
PLATFORMS = {
    "youtube": {"size": (1280, 720), "orient": "h", "max_px": 170, "tiny": 168, "budget": 0.30,
                "box": {"left": (0.05, 0.07, 0.60, 0.93), "right": (0.40, 0.07, 0.95, 0.76),
                        "top": (0.05, 0.06, 0.95, 0.44), "bottom": (0.05, 0.54, 0.74, 0.94)},
                "forbid": [(0.76, 0.78, 1.0, 1.0)]},
    "shorts":  {"size": (1080, 1920), "orient": "v", "max_px": 210, "tiny": 180, "budget": 0.16,
                "box": {"top": (0.06, 0.16, 0.80, 0.43), "bottom": (0.06, 0.43, 0.80, 0.70)},
                "forbid": [(0.0, 0.0, 1.0, 0.16), (0.80, 0.0, 1.0, 1.0), (0.0, 0.70, 1.0, 1.0)]},
    "reel":    {"size": (1080, 1920), "orient": "v", "max_px": 210, "tiny": 130, "budget": 0.16,
                "box": {"top": (0.06, 0.16, 0.80, 0.43), "bottom": (0.06, 0.43, 0.80, 0.70)},
                "forbid": [(0.0, 0.0, 1.0, 0.16), (0.80, 0.0, 1.0, 1.0), (0.0, 0.70, 1.0, 1.0)]},
    "feed":    {"size": (1080, 1350), "orient": "v", "max_px": 190, "tiny": 130, "budget": 0.22,
                "box": {"top": (0.06, 0.06, 0.94, 0.46), "bottom": (0.06, 0.54, 0.94, 0.94)},
                "forbid": []},
}
ALIASES = {"yt": "youtube", "youtube_long": "youtube", "long": "youtube", "thumbnail": "youtube",
           "short": "shorts", "youtube_shorts": "shorts",
           "instagram_reel": "reel", "reels": "reel", "ig_reel": "reel",
           "instagram_feed": "feed", "instagram_post": "feed", "post": "feed", "ig_feed": "feed"}

HOOK_MAX_LINES, HOOK_MAX_WORDS, HOOK_MAX_LINE_CHARS = 3, 7, 18
EYEBROW_MAX_WORDS, EYEBROW_MAX_CHARS = 4, 28
STOPWORDS = {"a", "an", "the", "to", "of", "in", "on", "my", "and", "or", "for", "with", "at", "is", "vs", "ka",
             "ki", "ke", "se", "me", "aur"}
MIN_CAP_AT_TINY = 7.0     # px of hook cap height at the smallest real display size
MIN_CONTRAST = 3.0         # WCAG large-text AA, hard floor; the scrim aims for 4.5
TARGET_CONTRAST = 4.5

FONT_STACKS = {
    # heavy grotesque: the default, closest to most top-channel thumbnails
    "heavy": ["Inter-Black", "Inter-ExtraBold", "Montserrat-Black", "seguibl.ttf", "ariblk.ttf",
              "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial Black.ttf"],
    # condensed: more letters per line at a bigger size; good for 9:16
    "condensed": ["Anton-Regular", "Oswald-Bold", "BebasNeue-Regular", "bahnschrift.ttf#Bold Condensed",
                  "impact.ttf", "DejaVuSansCondensed-Bold.ttf", "LiberationSansNarrow-Bold.ttf", "Impact.ttf"],
    "clean": ["Inter-Bold", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"],
}
DEVANAGARI = ["NotoSansDevanagari-Bold", "NirmalaB.ttf", "Nirmala.ttc#1", "NotoSansDevanagari-Bold.ttf"]


class Refused(Exception):
    pass


# ================================================================ utilities
def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, **kw)


def need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        sys.exit(f"error: {tool} not found on PATH")
    return path


def font_dirs() -> list[Path]:
    win = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    local = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts"
    return [SKILL_DIR / "assets" / "fonts", win, local, Path.home() / ".fonts",
            Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/truetype/liberation"),
            Path("/usr/share/fonts/truetype/noto"), Path("/usr/share/fonts/truetype"),
            Path("/Library/Fonts"), Path("/System/Library/Fonts/Supplemental")]


_FONT_CACHE: dict = {}


def resolve_font(style: str, text: str) -> tuple[str, str | None]:
    key = (style, any("\u0900" <= c <= "\u097F" for c in text))
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    if Path(style).suffix.lower() in (".ttf", ".otf", ".ttc") and Path(style).is_file():
        _FONT_CACHE[key] = (style, None)
        return _FONT_CACHE[key]
    names = DEVANAGARI if key[1] else FONT_STACKS.get(style, FONT_STACKS["heavy"]) + FONT_STACKS["clean"]
    for entry in names:
        name, _, var = entry.partition("#")
        for d in font_dirs():
            if not d.is_dir():
                continue
            hits = [d / name] if Path(name).suffix else sorted(d.glob(name + ".[ot]tf"))
            for p in hits:
                if p.is_file():
                    _FONT_CACHE[key] = (str(p), var or None)
                    return _FONT_CACHE[key]
    raise SystemExit("error: no bold sans font found; put Inter-Black.ttf in assets/fonts/")


def load_font(px: int, text: str, style: str = "heavy") -> ImageFont.FreeTypeFont:
    path, var = resolve_font(style, text)
    if var and var.isdigit():          # face index inside a .ttc collection
        return ImageFont.truetype(path, px, index=int(var))
    f = ImageFont.truetype(path, px)
    if var:
        try:
            f.set_variation_by_name(var)
        except Exception:
            pass
    return f


def srgb_lum(rgb: np.ndarray) -> np.ndarray:
    c = rgb / 255.0
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def contrast(l1: float, l2: float) -> float:
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def blur_np(a: np.ndarray, radius: float) -> np.ndarray:
    lo, hi = float(a.min()), float(a.max())
    if hi - lo < 1e-9:
        return a.copy()
    im = Image.fromarray(((a - lo) / (hi - lo) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255 * (hi - lo) + lo


def saliency(img: Image.Image, width: int = 160) -> np.ndarray:
    """Spectral-residual + colour-contrast saliency, normalised to sum 1. Cheap, no model."""
    h = max(8, round(img.height * width / img.width))
    small = img.convert("RGB").resize((width, h), Image.BILINEAR)
    g = np.asarray(small.convert("L"), dtype=np.float32) / 255
    F = np.fft.fft2(g)
    logA = np.log(np.abs(F) + 1e-6)
    k = np.ones((3, 3)) / 9
    pad = np.pad(logA, 1, mode="wrap")
    avg = sum(pad[i:i + logA.shape[0], j:j + logA.shape[1]] * k[i, j] for i in range(3) for j in range(3))
    sr = np.abs(np.fft.ifft2(np.exp((logA - avg) + 1j * np.angle(F)))) ** 2
    sr = blur_np(sr.astype(np.float32), 3)
    lab = np.asarray(small.convert("LAB"), dtype=np.float32)
    cc = np.sqrt(((lab - lab.reshape(-1, 3).mean(0)) ** 2).sum(-1))
    cc = blur_np(cc, 4)
    sat = np.asarray(small.convert("HSV"), dtype=np.float32)[..., 1] / 255
    s = sr / (sr.max() + 1e-9) * 0.45 + cc / (cc.max() + 1e-9) * 0.4 + blur_np(sat, 3) * 0.15
    yy, xx = np.mgrid[0:h, 0:width]
    s *= 1 - 0.35 * (((xx / width - 0.5) ** 2 + (yy / h - 0.5) ** 2) / 0.5)   # mild centre prior
    s = np.clip(s - np.percentile(s, 55), 0, None)
    return s / (s.sum() + 1e-9)


# ================================================================ probe + audio
def probe(video: Path) -> dict:
    r = run([need("ffprobe"), "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
             str(video)], text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"error: ffprobe failed: {r.stderr.strip()}")
    data = json.loads(r.stdout)
    fmt = data.get("format", {})
    v = next((s for s in data["streams"] if s.get("codec_type") == "video"), None)
    a = next((s for s in data["streams"] if s.get("codec_type") == "audio"), None)
    if v is None:
        sys.exit("error: no video stream")

    def rate(s):
        try:
            n, d = (s or "0/0").split("/")
            return round(int(n) / int(d), 3) if int(d) else None
        except ValueError:
            return None

    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    rot = rot or int((v.get("tags") or {}).get("rotate", 0) or 0)
    w, h = int(v["width"]), int(v["height"])
    if abs(rot) % 180 == 90:
        w, h = h, w
    return {"file": str(video), "duration_s": round(float(fmt.get("duration") or v.get("duration") or 0), 3),
            "width": w, "height": h, "rotation": rot,
            "fps": rate(v.get("avg_frame_rate")) or rate(v.get("r_frame_rate")),
            "video_codec": v.get("codec_name"), "pix_fmt": v.get("pix_fmt"),
            "bitrate_bps": int(fmt["bit_rate"]) if fmt.get("bit_rate") else None,
            "video_bitrate_bps": int(v["bit_rate"]) if v.get("bit_rate") else None,
            "size_bytes": int(fmt["size"]) if fmt.get("size") else None,
            "audio": None if a is None else {"codec": a.get("codec_name"), "channels": a.get("channels"),
                                             "sample_rate": a.get("sample_rate")}}


def measure_audio(video: Path, duration: float) -> dict:
    r = run([need("ffmpeg"), "-hide_banner", "-nostats", "-i", str(video), "-vn", "-sn", "-dn",
             "-af", "volumedetect,silencedetect=noise=-50dB:d=0.5,ebur128=framelog=quiet", "-f", "null", "-"],
            text=True, encoding="utf-8", errors="replace")
    err = r.stderr

    def num(pat):
        m = re.findall(pat, err)
        try:
            return float(m[-1]) if m else None
        except ValueError:
            return -120.0

    mean_db = num(r"mean_volume:\s*(-?[\d.]+|-inf) dB")
    starts = [float(x) for x in re.findall(r"silence_start:\s*(-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*(-?[\d.]+)", err)]
    silent = sum(e - s for s, e in zip(starts, ends))
    if len(starts) > len(ends):
        silent += max(0.0, duration - starts[-1])
    ratio = round(min(1.0, silent / duration), 3) if duration else None
    return {"present": True, "mean_volume_db": mean_db, "max_volume_db": num(r"max_volume:\s*(-?[\d.]+) dB"),
            "integrated_lufs": num(r"I:\s*(-?[\d.]+) LUFS"), "silence_ratio": ratio, "silence_threshold_db": -50,
            "real_audio": bool(mean_db is not None and mean_db > -50 and ratio is not None and ratio < 0.8),
            "note": "measurement only; no transcription. real_audio=true means sound exists, not what it is."}


def grab(video: Path, t: float, out: Path) -> None:
    """Decode one full-resolution frame at t (accurate seek). Writes an image; the video is untouched."""
    args = [need("ffmpeg"), "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1"]
    args += ["-q:v", "2"] if out.suffix.lower() in (".jpg", ".jpeg") else []
    r = run(args + ["-y", str(out)])
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"frame grab failed at {t:.3f}s: {r.stderr.decode(errors='replace').strip()}")


# ================================================================ analyze
def decode_lowres(video: Path, meta: dict, fps: float, width: int, window, mode: str = "auto",
                  target: int = 160) -> tuple[list[float], np.ndarray, str]:
    """One decode pass to small RGB frames. Software decode: GPU decode + download is slower at this size."""
    w = width
    h = max(2, round(meta["height"] * w / meta["width"] / 2) * 2)
    start = window[0] if window else 0.0
    span = (window[1] - window[0]) if window else meta["duration_s"]
    seek = ["-ss", f"{start:.3f}", "-t", f"{span:.3f}"] if window else []
    # heavy input (above ~1080p x 90 s): decode keyframes only, ~5-10x faster, ~1 sample/s on phone footage
    heavy = meta["width"] * meta["height"] * span > 1920 * 1080 * 90
    if heavy and mode != "dense":
        every = max(1, math.ceil(span / 1.0 / max(1, target)))      # assume ~1 keyframe/s; cap the count
        vf = f"select='not(mod(n\\,{every}))',scale={w}:{h}:flags=area,showinfo"
        cmd = [need("ffmpeg"), "-v", "info", "-skip_frame", "nokey", *seek, "-i", str(video), "-an", "-sn", "-dn",
               "-vf", vf, "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        r = run(cmd)
        times = [start + float(x) for x in re.findall(rb"pts_time:\s*([\d.]+)", r.stderr)]
        n = len(r.stdout) // (w * h * 3)
        if n >= 12 and len(times) >= n:
            frames = np.frombuffer(r.stdout, dtype=np.uint8)[: n * w * h * 3].reshape(n, h, w, 3)
            return [round(t, 3) for t in times[:n]], frames, "keyframes"
    vf = f"fps={fps:.5f},scale={w}:{h}:flags=area"
    r = run([need("ffmpeg"), "-v", "error", *seek, "-i", str(video), "-an", "-sn", "-dn",
             "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    n = len(r.stdout) // (w * h * 3)
    if n == 0:
        raise SystemExit(f"error: could not decode frames: {r.stderr.decode(errors='replace')[-400:]}")
    frames = np.frombuffer(r.stdout, dtype=np.uint8)[: n * w * h * 3].reshape(n, h, w, 3)
    times = [start + i / fps for i in range(n)]      # fps filter emits the frame nearest i/fps
    return [round(float(t), 3) for t in times], frames, f"{fps:.2f} fps"


def ocr_images(paths: list[Path]) -> dict[str, list[dict]] | None:
    """Optional OCR for burned-in text: Windows built-in OCR, else tesseract, else None (vision only)."""
    if not paths:
        return {}
    ps1 = SKILL_DIR / "scripts" / "ocr_windows.ps1"
    pwsh = shutil.which("powershell.exe") or shutil.which("powershell")
    if os.name == "nt" and pwsh and ps1.is_file():
        r = run([pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1), *map(str, paths)],
                text=True, encoding="utf-8", errors="replace")
        res = {}
        for line in r.stdout.splitlines():
            try:
                j = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "error" in j and "path" not in j:
                return None
            if "path" in j:
                res[str(Path(j["path"]).name)] = [{"text": l["text"], "box": l["box"]} for l in j.get("lines", [])]
        return res if res else None
    tess = shutil.which("tesseract")
    if tess:
        res = {}
        for p in paths:
            r = run([tess, str(p), "stdout", "--psm", "11", "tsv"], text=True, encoding="utf-8", errors="replace")
            lines = []
            for row in r.stdout.splitlines()[1:]:
                c = row.split("\t")
                if len(c) == 12 and c[11].strip() and float(c[10] or -1) > 50:
                    x, y, w, h = map(int, c[6:10])
                    lines.append({"text": c[11].strip(), "box": [x, y, x + w, y + h]})
            res[p.name] = lines
        return res
    return None


def overlay_text(lines: list[dict], w: int, h: int) -> list[str]:
    """Large text = editor overlay/title/logo. Small text (posters, labels in the scene) is ignored."""
    hits = []
    for l in lines:
        x0, y0, x1, y1 = l["box"]
        alnum = sum(ch.isalnum() for ch in l["text"])
        if alnum >= 3 and ((y1 - y0) >= 0.022 * h or ((x1 - x0) >= 0.25 * w and (y1 - y0) >= 0.014 * h)):
            hits.append(l["text"])
    return hits


def content_box(rgb: np.ndarray) -> tuple[int, int, int, int]:
    """Bounding box inside black (or flat) bars added by an edit, e.g. a zoomed-out clip. (x0, y0, x1, y1)"""
    g = rgb.astype(np.float32).mean(-1) / 255
    h, w = g.shape

    def flat(v_mean, v_std):
        return (v_mean < 0.07) & (v_std < 0.035)

    rows = flat(g.mean(1), g.std(1))
    cols = flat(g.mean(0), g.std(0))
    y0 = int(np.argmax(~rows)) if (~rows).any() else 0
    y1 = h - int(np.argmax(~rows[::-1])) if (~rows).any() else h
    x0 = int(np.argmax(~cols)) if (~cols).any() else 0
    x1 = w - int(np.argmax(~cols[::-1])) if (~cols).any() else w
    # ignore slivers; a real bar is at least 1.5% of the side
    y0 = y0 if y0 >= 0.015 * h else 0
    y1 = y1 if h - y1 >= 0.015 * h else h
    x0 = x0 if x0 >= 0.015 * w else 0
    x1 = x1 if w - x1 >= 0.015 * w else w
    return x0, y0, x1, y1


def metrics(rgb: np.ndarray) -> dict:
    g = (rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114).astype(np.float32) / 255
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    f = rgb.astype(np.float32)
    rg = f[..., 0] - f[..., 1]
    yb = 0.5 * (f[..., 0] + f[..., 1]) - f[..., 2]
    colorful = (math.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * math.sqrt(rg.mean() ** 2 + yb.mean() ** 2)) / 100
    return {"sharpness": float(lap.var() * 1000), "brightness": float(g.mean()), "contrast": float(g.std()),
            "colorfulness": float(colorful), "clip_hi": float((g > 0.98).mean()), "clip_lo": float((g < 0.02).mean())}


def cmd_analyze(a: argparse.Namespace) -> None:
    video = Path(a.video).resolve()
    if not video.is_file():
        sys.exit(f"error: video not found: {video}")
    out = Path(a.out).resolve()
    (out / "frames").mkdir(parents=True, exist_ok=True)
    for old in (out / "frames").glob("*.jpg"):
        old.unlink()

    meta = probe(video)
    dur = meta["duration_s"] or 1.0
    bg = ThreadPoolExecutor(max_workers=4)
    audio_job = bg.submit(measure_audio, video, dur) if meta["audio"] else None
    window = None
    if a.window:
        s, e = (float(x) for x in a.window.split("-"))
        window = (max(0.0, s), min(dur, e))
    span = (window[1] - window[0]) if window else dur
    target = a.samples or 160
    fps = min(12.0 if window else 4.0, max(0.05, target / span))   # a window may sample densely
    lw = 480 if meta["width"] >= meta["height"] else 360   # big enough for overlay OCR
    times, frames, sampling_mode = decode_lowres(video, meta, fps, lw, window, "dense" if a.dense else "auto", target)

    samples = []
    prev = None
    for i, (t, fr) in enumerate(zip(times, frames)):
        m = metrics(fr)
        g = fr.mean(-1).astype(np.float32) / 255
        m["change_prev"] = None if prev is None else float(np.abs(g - prev).mean())
        prev = g
        samples.append({"i": i, "t": t, **m})
    # transition / fade: big change on both sides of a soft frame
    for i, s in enumerate(samples):
        nxt = samples[i + 1]["change_prev"] if i + 1 < len(samples) else None
        s["transition"] = bool(s["change_prev"] and nxt and s["change_prev"] > 0.06 and nxt > 0.06)

    def norm(key):
        v = np.array([s[key] for s in samples], dtype=np.float64)
        lo, hi = np.percentile(v, 5), np.percentile(v, 95)
        return np.clip((v - lo) / (hi - lo), 0, 1) if hi > lo else np.full_like(v, 0.5)

    sh, co, cf = norm("sharpness"), norm("contrast"), norm("colorfulness")
    for s, a1, b1, c1 in zip(samples, sh, co, cf):
        b = s["brightness"]
        # moody low-key shots are fine; only truly underexposed or washed-out frames lose points
        exposure = 1.0 if 0.14 <= b <= 0.78 else max(0.0, 1 - (0.14 - b) / 0.14 if b < 0.14 else 1 - (b - 0.78) / 0.22)
        clip_pen = min(1.0, (s["clip_hi"] * 1.5 + max(0.0, s["clip_lo"] - 0.15)) * 4)
        s["score"] = round(0.36 * a1 + 0.16 * b1 + 0.30 * c1 + 0.18 * exposure - 0.25 * clip_pen
                           - (0.3 if s["transition"] else 0), 4)
        flags = []
        if a1 < 0.15:
            flags.append("soft")
        if s["brightness"] < 0.10:
            flags.append("dark")
        if s["clip_hi"] > 0.08:
            flags.append("blown")
        if s["transition"]:
            flags.append("transition")
        cb = content_box(frames[s["i"]])
        if cb != (0, 0, frames.shape[2], frames.shape[1]):
            flags.append("bars")
        s["flags"] = flags

    # Candidate search. The pool grows in score order (time-spaced only), each batch is OCR'd together
    # with its neighbours, and look-alike suppression runs only after the text check, so a clean frame is
    # never dropped for resembling a higher-scoring frame that carries an overlay.
    order = sorted(range(len(samples)), key=lambda i: samples[i]["score"], reverse=True)
    pool_gap = max(0.2, span / 150)
    min_gap = max(0.25 if window else 0.6, span / 50)
    grays = {}
    hits_at: dict[int, list[str]] = {}
    ocr_used = None if not a.no_ocr else False
    hh, ww = frames.shape[1] * 2, frames.shape[2] * 2
    tmp = Path(tempfile.mkdtemp(prefix="vp_ocr_"))

    def tier(i):
        f = samples[i]["flags"]
        return 2 if "overlay-text" in f else 1 if "overlay-near" in f else 0

    def pick(pool):
        picked = []
        for i in sorted(pool, key=lambda i: (tier(i), -samples[i]["score"])):
            if len(picked) >= a.candidates:
                break
            if i not in grays:
                grays[i] = frames[i][::2, ::2].mean(-1).astype(np.float32) / 255
            if any(abs(samples[i]["t"] - samples[j]["t"]) < min_gap or
                   (tier(i) == tier(j) and np.abs(grays[i] - grays[j]).mean() < 0.02) for j in picked):
                continue
            picked.append(i)
        return picked

    pool: list[int] = []
    cursor = 0
    try:
        for _round in range(5):
            batch = []
            while cursor < len(order) and len(batch) < max(16, a.candidates * 2):
                i = order[cursor]
                cursor += 1
                if all(abs(samples[i]["t"] - samples[j]["t"]) >= pool_gap for j in pool + batch):
                    batch.append(i)
            if not batch:
                break
            pool += batch
            if ocr_used is not False:
                todo = sorted({j for i in batch for j in (i - 1, i, i + 1)
                               if 0 <= j < len(samples) and j not in hits_at})
                paths = []
                for j in todo:
                    p = tmp / f"s{j:04d}.png"
                    im = Image.fromarray(frames[j])
                    im.resize((im.width * 2, im.height * 2), Image.LANCZOS).save(p)  # 2x lifts OCR recall
                    paths.append(p)
                ocr = ocr_images(paths)
                if ocr is None:
                    ocr_used = False
                else:
                    ocr_used = True
                    for j in todo:
                        hits_at[j] = overlay_text(ocr.get(f"s{j:04d}.png", []), ww, hh)
            for i in batch:
                own = hits_at.get(i, [])
                near = [t for j in (i - 1, i + 1) for t in hits_at.get(j, [])]
                samples[i]["overlay_text"] = own or near
                if own:
                    samples[i]["flags"].append("overlay-text")
                elif near:
                    samples[i]["flags"].append("overlay-near")
            picked = pick(pool)
            if sum(1 for i in picked if tier(i) == 0) >= min(a.candidates, 6) or cursor >= len(order):
                break
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    picked = pick(pool)

    jobs = []
    for rank, i in enumerate(picked, 1):
        p = out / "frames" / f"cand{rank:02d}_t{samples[i]['t']:08.3f}s.jpg"
        jobs.append((rank, i, p, bg.submit(grab, video, samples[i]["t"], p)))
    cands = []
    for rank, i, p, job in jobs:
        job.result()
        s = samples[i]
        cands.append({"id": f"C{rank}", "t": s["t"], "score": s["score"], "flags": s["flags"], "path": str(p),
                      "overlay_text": s.get("overlay_text", []), "brightness": round(s["brightness"], 3),
                      "sharpness": round(s["sharpness"], 2), "colorfulness": round(s["colorfulness"], 3)})
    seen_text = []
    for i in sorted(pool, key=lambda i: samples[i]["t"]):
        for tx in samples[i].get("overlay_text", []):
            if tx not in [x["text"] for x in seen_text]:
                seen_text.append({"t": samples[i]["t"], "text": tx})

    sheet_idx = list(np.linspace(0, len(samples) - 1, min(24, len(samples))).round().astype(int))
    build_sheet([(Image.fromarray(frames[i]), f"{samples[i]['t']:.2f}s") for i in sheet_idx],
                f"{video.name}  {meta['duration_s']}s  {meta['width']}x{meta['height']}  {meta['fps']}fps  "
                f"{meta['video_codec']}  (timeline)", out / "contact_sheet.jpg",
                cols=6 if meta["height"] > meta["width"] else 4, tile_w=200 if meta["height"] > meta["width"] else 320)
    build_sheet([(Image.open(c["path"]), f"{c['id']}  {c['t']:.2f}s  q{c['score']:.2f}"
                  + (f"  {','.join(c['flags'])}" if c["flags"] else "")) for c in cands],
                "Candidates: reject any with burned-in text/logos/stickers, transitions, motion blur, closed eyes",
                out / "candidates.jpg", cols=4, tile_w=300 if meta["height"] > meta["width"] else 460)

    changes = sorted((s for s in samples if s["change_prev"]), key=lambda s: s["change_prev"], reverse=True)
    big, used = [], []
    for s in changes:
        if all(abs(s["t"] - u) > min_gap * 2 for u in used):
            big.append({"at_t": s["t"], "mean_abs_diff": round(s["change_prev"], 4)})
            used.append(s["t"])
        if len(big) == 5:
            break
    audio = audio_job.result() if audio_job else {"present": False, "real_audio": False,
                                                              "note": "no audio stream: silent"}
    report = {
        "video": meta,
        "sampling": {"samples": len(samples), "mode": sampling_mode, "window": window,
                     "method": "single low-res decode pass; candidates re-extracted at full res with accurate seek"},
        "candidates_sheet": str(out / "candidates.jpg"), "contact_sheet": str(out / "contact_sheet.jpg"),
        "candidates": cands,
        "ocr": {"used": ocr_used, "overlay_text_seen": seen_text,
                "note": "OCR flags large burned-in text only; it can misread stylised logos. Your eyes decide."},
        "largest_changes": sorted(big, key=lambda b: b["at_t"]),
        "audio": audio,
        "next": "Open candidates.jpg and contact_sheet.jpg. Pick a clean candidate by eye before any copy.",
    }
    (out / "analysis.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"analysis": str(out / "analysis.json"), "candidates_sheet": report["candidates_sheet"],
                      "contact_sheet": report["contact_sheet"],
                      "video": f"{meta['duration_s']}s {meta['width']}x{meta['height']} {meta['fps']}fps "
                               f"{meta['video_codec']} {meta['pix_fmt']}",
                      "samples": f"{len(samples)} ({sampling_mode})",
                      "candidates": [f"{c['id']} {c['t']:.2f}s q{c['score']:.2f} {' '.join(c['flags'])}".strip()
                                     for c in cands],
                      "ocr_used": ocr_used,
                      "overlay_text_seen": [f"{x['t']:.1f}s {x['text']}" for x in seen_text][:12],
                      "largest_changes_s": [b["at_t"] for b in report["largest_changes"]],
                      "audio": {k: audio.get(k) for k in ("present", "real_audio", "mean_volume_db",
                                                          "integrated_lufs", "silence_ratio")}}, indent=1))


def build_sheet(tiles: list[tuple[Image.Image, str]], title: str, out: Path, cols: int, tile_w: int) -> None:
    if not tiles:
        return
    ar = tiles[0][0].height / tiles[0][0].width
    th = round(tile_w * ar)
    rows = math.ceil(len(tiles) / cols)
    pad, head = 6, 40
    sheet = Image.new("RGB", (cols * (tile_w + pad) + pad, head + rows * (th + pad) + pad), (18, 18, 18))
    d = ImageDraw.Draw(sheet)
    fh, fl = load_font(18, "a", "clean"), load_font(15, "a", "clean")
    d.text((pad, 11), title, font=fh, fill=(235, 235, 235))
    for k, (img, label) in enumerate(tiles):
        x = pad + (k % cols) * (tile_w + pad)
        y = head + (k // cols) * (th + pad)
        sheet.paste(img.convert("RGB").resize((tile_w, th), Image.LANCZOS), (x, y))
        d.rectangle([x, y, x + 10 + d.textlength(label, font=fl), y + 21], fill=(0, 0, 0))
        d.text((x + 5, y + 2), label, font=fl, fill=(255, 255, 255))
    sheet.save(out, "JPEG", quality=84)


# ================================================================ render helpers
def is_emoji(ch: str) -> bool:
    o = ord(ch)
    return unicodedata.category(ch) == "So" or 0x1F000 <= o <= 0x1FAFF or 0x2600 <= o <= 0x27BF or ch in "\u200d\ufe0f"


def check_copy(hook_lines: list[str], eyebrow: str) -> None:
    problems = []
    if not hook_lines:
        problems.append("hook is empty")
    if len(hook_lines) > HOOK_MAX_LINES:
        problems.append(f"hook has {len(hook_lines)} lines; max {HOOK_MAX_LINES}")
    words = sum(len(l.split()) for l in hook_lines)
    if words > HOOK_MAX_WORDS:
        problems.append(f"hook has {words} words; max {HOOK_MAX_WORDS}")
    for l in hook_lines:
        if len(l) > HOOK_MAX_LINE_CHARS:
            problems.append(f"hook line '{l}' is {len(l)} chars; max {HOOK_MAX_LINE_CHARS}")
    if eyebrow and (len(eyebrow.split()) > EYEBROW_MAX_WORDS or len(eyebrow) > EYEBROW_MAX_CHARS):
        problems.append(f"eyebrow '{eyebrow}' exceeds {EYEBROW_MAX_WORDS} words / {EYEBROW_MAX_CHARS} chars")
    if any(is_emoji(ch) for ch in "".join(hook_lines) + eyebrow):
        problems.append("emoji are not allowed on the thumbnail")
    if re.search("[ि्]", "".join(hook_lines) + eyebrow) and not features.check("raqm"):
        raise Refused("this Devanagari text needs complex shaping (ि or a half-letter) and Pillow here has no "
                      "raqm, so it would render wrongly. Use a Roman/Hinglish hook, or the Canva path.")
    if problems:
        raise Refused("; ".join(problems) + ". Rewrite the copy; it will not be shrunk to fit.")


def wrap(text: str, limit: int) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > limit:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + ([cur] if cur else [])


def split_hook(hook) -> tuple[list[str], list[list[str]]]:
    """(lines used for the limit check, candidate layouts). Explicit breaks are kept as given."""
    if isinstance(hook, list):
        lines = [str(x).strip() for x in hook if str(x).strip()]
        return lines, [lines]
    text = str(hook).strip()
    if re.search(r"[\n|]", text):
        lines = [x.strip() for x in re.split(r"[\n|]", text) if x.strip()]
        return lines, [lines]
    text = " ".join(text.split())
    base = wrap(text, HOOK_MAX_LINE_CHARS)
    words = text.split()
    if len(words) > HOOK_MAX_WORDS:
        return base, [base]
    # every way to break <=7 words into <=3 lines (at most 22 layouts); the fitter picks the best one
    cands = []
    n = len(words)
    for k in range(0, min(HOOK_MAX_LINES, n)):
        for cuts in itertools.combinations(range(1, n), k):
            idx = (0, *cuts, n)
            c = [" ".join(words[idx[j]:idx[j + 1]]) for j in range(len(idx) - 1)]
            if all(len(l) <= HOOK_MAX_LINE_CHARS for l in c):
                cands.append(c)
    return base, cands or [base]


def plan_crop(frame: Image.Image, spec: dict, rects: dict, focus) -> tuple[tuple, str, dict]:
    """Choose crop window + layout together. rects = {layout: (x0, y0, x1, y1)} of the real text block as
    fractions of the canvas. Keep the subject in frame, uncut, and out from under the type."""
    W, H = spec["size"]
    ar = W / H
    fw, fh = frame.size
    cw, ch = (fh * ar, fh) if fw / fh > ar else (fw, fw / ar)
    sal = saliency(frame)
    sh_, sw_ = sal.shape
    kx, ky = sw_ / fw, sh_ / fh
    ii = np.pad(sal.cumsum(0).cumsum(1), ((1, 0), (1, 0)))

    def mass(x0, y0, x1, y1):
        x0, y0 = min(sw_, max(0, int(round(x0 * kx)))), min(sh_, max(0, int(round(y0 * ky))))
        x1, y1 = min(sw_, max(0, int(round(x1 * kx)))), min(sh_, max(0, int(round(y1 * ky))))
        if x1 <= x0 or y1 <= y0:
            return 0.0
        return float(ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0])

    if focus and focus != "auto":
        fx, fy = float(focus[0]), float(focus[1])
        xs = [min(max(0.0, fx * fw - cw / 2), fw - cw)]
        ys = [min(max(0.0, fy * fh - ch / 2), fh - ch)]
    else:
        xs = list(np.linspace(0, fw - cw, 31)) if fw - cw > 1 else [0.0]
        ys = list(np.linspace(0, fh - ch, 31)) if fh - ch > 1 else [0.0]
    best = None
    for side, (rx0, ry0, rx1, ry1) in rects.items():
        for x in xs:
            for y in ys:
                inside = mass(x, y, x + cw, y + ch)
                under = mass(x + rx0 * cw, y + ry0 * ch, x + rx1 * cw, y + ry1 * ch)
                edge = (mass(x, y, x + 0.03 * cw, y + ch) + mass(x + 0.97 * cw, y, x + cw, y + ch)
                        + mass(x, y, x + cw, y + 0.03 * ch) + mass(x, y + 0.97 * ch, x + cw, y + ch))
                score = inside - 1.6 * under - 0.6 * edge
                if best is None or score > best[0]:
                    best = (score, (x, y, x + cw, y + ch), side, inside, under)
    _, box, side, inside, under = best
    return box, side, {"subject_in_crop": round(inside, 3),
                       "subject_under_type": round(under / max(inside, 1e-6), 3)}


def grade(img: Image.Image, mode: str, upscale: float) -> Image.Image:
    if mode == "none":
        return img
    a = np.asarray(img, dtype=np.float32) / 255
    y = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    lo, hi = np.percentile(y, 0.4), np.percentile(y, 99.6)
    lo, hi = min(lo, 0.08), max(hi, 0.90)          # never stretch more than ~1.2x
    a = np.clip((a - lo) / (hi - lo), 0, 1)
    s = a * a * (3 - 2 * a)                         # gentle S-curve
    a = a * 0.86 + s * 0.14
    y = (a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32))[..., None]
    sat = a.max(-1, keepdims=True) - a.min(-1, keepdims=True)
    a = np.clip(y + (a - y) * (1 + 0.28 * (1 - sat)), 0, 1)   # vibrance: lift muted colours more
    out = Image.fromarray((a * 255 + 0.5).astype(np.uint8))
    return out.filter(ImageFilter.UnsharpMask(radius=1.6 if upscale > 1.15 else 1.0,
                                              percent=70 if upscale > 1.15 else 35, threshold=2))


def accent_from(img: Image.Image) -> tuple[str, str]:
    small = img.convert("RGB").resize((200, max(1, round(img.height * 200 / img.width))))
    hsv = np.asarray(small.convert("HSV"), dtype=np.float32) / 255.0
    rgb = np.asarray(small, dtype=np.float32)
    mask = (hsv[..., 1] > 0.45) & (hsv[..., 2] > 0.35)
    if mask.sum() < 0.01 * mask.size:
        return "#FFD84A", "no saturated colour in frame; warm yellow used"
    hb = (hsv[..., 0] * 36).astype(int) % 36
    weights = np.bincount(hb[mask], weights=hsv[..., 1][mask] * hsv[..., 2][mask], minlength=36)
    top = int(weights.argmax())
    r, g, b = rgb[mask & (hb == top)].mean(axis=0)
    hh, ss, vv = Image.new("RGB", (1, 1), (int(r), int(g), int(b))).convert("HSV").getpixel((0, 0))
    lifted = Image.new("HSV", (1, 1), (hh, max(ss, 170), 255)).convert("RGB").getpixel((0, 0))
    return "#%02X%02X%02X" % lifted, "dominant saturated hue of the frame, lifted for legibility"


def scrim(canvas: Image.Image, side: str, strength: float, band: tuple) -> Image.Image:
    W, H = canvas.size
    x0, y0, x1, y1 = band
    if side in ("left", "right"):
        xs = np.arange(W, dtype=np.float32)
        dist = np.maximum(0, xs - (x1 + 0.03 * W)) if side == "left" else np.maximum(0, (x0 - 0.03 * W) - xs)
        a = np.tile(np.clip(1 - dist / (0.30 * W), 0, 1) ** 1.5, (H, 1))
    else:
        ys = np.arange(H, dtype=np.float32)
        dist = np.maximum(0, np.maximum((y0 - 0.05 * H) - ys, ys - (y1 + 0.05 * H)))
        a = np.tile((np.clip(1 - dist / (0.17 * H), 0, 1) ** 1.5)[:, None], (1, W))
    a = 0.06 + (strength - 0.06) * a
    arr = np.asarray(canvas, dtype=np.float32) * (1 - a[..., None])
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


def boxes_overlap(a, b) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


# ================================================================ preview sheet
def preview_sheet(cover: Image.Image, plat: str, out: Path, type_bbox=None, type_box=None) -> None:
    spec = PLATFORMS[plat]
    W, H = spec["size"]
    big_h = 620
    big = cover.resize((round(W * big_h / H), big_h), Image.LANCZOS).convert("RGBA")
    s = big_h / H
    ov = Image.new("RGBA", big.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x0, y0, x1, y1 in spec["forbid"]:
        d.rectangle([x0 * W * s, y0 * H * s, x1 * W * s, y1 * H * s], fill=(255, 40, 40, 70))
    if type_box:
        d.rectangle([v * s for v in type_box], outline=(60, 255, 120, 255), width=2)
    if type_bbox:
        d.rectangle([v * s for v in type_bbox], outline=(255, 220, 0, 255), width=2)
    big = Image.alpha_composite(big, ov).convert("RGB")

    lab = load_font(15, "a", "clean")
    badge_f = load_font(11, "a", "clean")

    def tile(width: int, crop34=False):
        im = cover
        if crop34:  # Instagram profile grid shows a centred 3:4
            hh = round(W * 4 / 3)
            top = (H - hh) // 2
            im = cover.crop((0, top, W, top + hh))
        t = im.resize((width, round(width * im.height / im.width)), Image.LANCZOS)
        if plat == "youtube":
            dd = ImageDraw.Draw(t)
            bw = dd.textlength("12:34", font=badge_f) + 8
            dd.rounded_rectangle([t.width - bw - 4, t.height - 18, t.width - 4, t.height - 4], 3, fill=(0, 0, 0))
            dd.text((t.width - bw, t.height - 17), "12:34", font=badge_f, fill=(255, 255, 255))
        return t

    if plat == "youtube":
        smalls = [("search 168", tile(168)), ("home 320", tile(320))]
    elif plat == "feed":
        smalls = [("grid 130", tile(130, crop34=True)), ("feed 360", tile(360))]
    else:
        smalls = [("shelf 180", tile(180)), ("grid 130 (3:4)", tile(130, crop34=True))]
    col_w = sum(t.width for _, t in smalls) + 30
    panel_h = max(t.height for _, t in smalls) + 34
    sheet = Image.new("RGB", (big.width + 24 + col_w + 12, max(big_h + 40, panel_h * 2 + 40)), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    d.text((12, 10), f"{plat} {W}x{H}  red=forbidden  green=type box  yellow=type", font=lab, fill=(230, 230, 230))
    sheet.paste(big, (12, 34))
    x0 = big.width + 24
    for k, (bg, name) in enumerate([((255, 255, 255), "light UI"), ((15, 15, 15), "dark UI")]):
        y0 = 34 + k * panel_h
        d.rectangle([x0, y0, x0 + col_w, y0 + panel_h - 6], fill=bg)
        x = x0 + 10
        for label, t in smalls:
            sheet.paste(t, (x, y0 + 22))
            d.text((x, y0 + 3), f"{label} · {name}", font=lab, fill=(120, 120, 120))
            x += t.width + 10
    sheet.save(out, "JPEG", quality=85)


def file_checks(path: Path, plat: str) -> dict:
    W, H = PLATFORMS[plat]["size"]
    im = Image.open(path)
    return {"format_jpeg": im.format == "JPEG", "dimensions": list(im.size) == [W, H],
            "under_2mb": path.stat().st_size < MAX_BYTES, "rgb": im.mode == "RGB"}


# ================================================================ render
def cmd_render(a: argparse.Namespace) -> None:
    brief_path = Path(a.brief).resolve()
    brief = json.loads(brief_path.read_text(encoding="utf-8"))
    base = brief_path.parent

    def rel(p: str) -> Path:
        q = Path(p)
        return q if q.is_absolute() else (base / q)

    plat = brief.get("platform")
    if isinstance(plat, list):
        raise Refused("one brief renders one platform; write a second brief only if the user asked for it")
    plat = ALIASES.get(str(plat).lower(), str(plat).lower())
    if plat not in PLATFORMS:
        raise Refused(f"unknown platform '{brief.get('platform')}'; use youtube, shorts, reel or feed")
    spec = PLATFORMS[plat]
    W, H = spec["size"]
    bg_only = bool(brief.get("background_only"))
    style = brief.get("font", "heavy")

    eyebrow = str(brief.get("eyebrow", "") or "").strip()
    if not bg_only:
        hook_lines, layouts = split_hook(brief.get("hook", ""))
        check_copy(hook_lines, eyebrow)
        if brief.get("uppercase", True):
            layouts = [[l.upper() for l in c] for c in layouts]
            eyebrow = eyebrow.upper()
    highlight = str(brief.get("highlight", "") or "").strip().upper()

    # --- the real frame
    tmpdir = None
    if brief.get("frame"):
        src = rel(brief["frame"])
        src_desc = str(src)
    elif brief.get("video") and brief.get("time") is not None:
        tmpdir = Path(tempfile.mkdtemp(prefix="vp_"))
        src = tmpdir / "frame.png"
        grab(rel(brief["video"]), float(brief["time"]), src)
        src_desc = f"{rel(brief['video'])} @ {float(brief['time']):.3f}s"
    else:
        raise Refused("brief needs 'frame' (an extracted frame) or 'video' + 'time'")
    if not src.is_file():
        raise Refused(f"frame not found: {src}")
    frame = Image.open(src).convert("RGB")
    trimmed = None
    if brief.get("trim_bars", True):
        cb = content_box(np.asarray(frame))
        if cb != (0, 0, frame.width, frame.height):
            trimmed = cb
            frame = frame.crop(cb)
    if tmpdir:
        shutil.rmtree(tmpdir, ignore_errors=True)

    side_req = brief.get("side", "auto")
    sides = list(spec["box"]) if side_req == "auto" else [side_req]
    if any(s not in spec["box"] for s in sides):
        raise Refused(f"side '{side_req}' invalid for {plat}; use one of {list(spec['box'])} or auto")
    out = rel(brief.get("out") or f"{plat}_cover.jpg")
    out.parent.mkdir(parents=True, exist_ok=True)
    warnings = []
    if trimmed:
        warnings.append(f"trimmed edit bars from the frame: kept {trimmed}")

    # --- fit type for every layout first (independent of the crop), so the crop search sees the real block
    lh = 1.0 if style == "condensed" else 1.04
    tiny_scale = spec["tiny"] / W
    budget = spec["budget"] * W * H

    def fit(lines, bw, bh):
        allt = " ".join(lines) + eyebrow
        for px in range(spec["max_px"], 39, -2):
            f = load_font(px, allt, style)
            hb = f.getbbox("H")
            if (hb[3] - hb[1]) * tiny_scale < MIN_CAP_AT_TINY:
                return None
            stroke = max(2, round(px * 0.045))
            bbs = [f.getbbox(l) for l in lines]
            body_h = px * lh * (len(lines) - 1) + max(b[3] for b in bbs) - bbs[0][1] + 2 * stroke
            ink_w = max(b[2] - b[0] for b in bbs) + 2 * stroke
            tag = None
            if eyebrow:
                ey_px = max(26, round(px * 0.27))
                ef = load_font(ey_px, allt, "clean")
                eb = ef.getbbox(eyebrow)
                pad_x, pad_y = round(ey_px * 0.45), round(ey_px * 0.28)
                tag = {"font": ef, "px": ey_px, "bbox": eb, "pad": (pad_x, pad_y),
                       "w": eb[2] - eb[0] + 2 * pad_x, "h": eb[3] - eb[1] + 2 * pad_y, "gap": round(px * 0.22)}
            total_h = body_h + (tag["h"] + tag["gap"] if tag else 0)
            text_w = max(ink_w, tag["w"] if tag else 0)
            if text_w <= bw and total_h <= bh and text_w * total_h <= budget:
                return {"lines": lines, "px": px, "font": f, "stroke": stroke, "bbs": bbs, "tag": tag,
                        "body_h": body_h, "total_h": total_h, "text_w": text_w, "cap": hb[3] - hb[1]}
        return None

    def geometry(side):
        bx0, by0, bx1, by1 = spec["box"][side]
        box = (bx0 * W, by0 * H, bx1 * W, by1 * H)
        bw, bh = box[2] - box[0], box[3] - box[1]
        fits = [g for g in (fit(l, bw, bh) for l in layouts) if g]
        if not fits:
            return None
        def quality(g):
            # bigger type wins; an extra line must buy >12%; a line ending on "to/the/my…" reads as broken
            dangling = sum(1 for l in g["lines"][:-1] if l.split()[-1].lower() in STOPWORDS)
            return g["px"] * 0.88 ** (len(g["lines"]) - 1) * 0.85 ** dangling, -len(g["lines"])

        g = max(fits, key=quality)
        g["box"], g["align_right"] = box, side == "right"
        if spec["orient"] == "h" and side in ("left", "right"):
            y_top = box[1] + (bh - g["total_h"]) / 2
        elif side == "bottom" and spec["orient"] == "h":
            y_top = box[3] - g["total_h"]
        else:
            y_top = box[1] + (bh - g["total_h"]) * (0.12 if side == "top" else 0.88)
        x0 = box[2] - g["text_w"] if g["align_right"] else box[0]
        g["rect"] = (x0, y_top, x0 + g["text_w"], y_top + g["total_h"])
        return g

    if bg_only:
        geoms = {}
        rects = {s: spec["box"][s] for s in sides}
    else:
        geoms = {}
        for s in sides:
            gs = geometry(s)
            if gs:
                geoms[s] = gs
        if not geoms:
            raise Refused(f"hook does not fit any {plat} layout at a size that reads on a {spec['tiny']}px-wide "
                          "phone tile within the text-area budget. Shorten it; it will not be shrunk further.")
        rects = {s: (g["rect"][0] / W, g["rect"][1] / H, g["rect"][2] / W, g["rect"][3] / H)
                 for s, g in geoms.items()}

    crop, side, subj = plan_crop(frame, spec, rects, brief.get("focus", "auto"))
    scale = W / (crop[2] - crop[0])
    base_img = frame.resize((W, H), Image.LANCZOS, box=crop)
    base_img = grade(base_img, brief.get("grade", "auto"), scale)
    sampled, accent_note = accent_from(base_img)
    accent = sampled
    if brief.get("accent") not in (None, "", "auto"):
        accent, accent_note = brief["accent"], "from brief"

    if scale > 1.0:
        warnings.append(f"upscaled x{scale:.2f} from the source frame (Lanczos + unsharp, no AI upscaler)")
    if scale > 2.2:
        warnings.append("upscale above 2.2x looks soft; prefer a higher-res source or a tighter subject")
    if subj["subject_under_type"] > 0.25:
        warnings.append(f"{subj['subject_under_type']:.0%} of the subject is under the type; "
                        "consider another frame, side or focus")

    if bg_only:
        # Canva shapes cannot do gradients, so the soft scrim is baked in here; Canva only carries the type
        bx = spec["box"][side]
        bake = float(brief.get("scrim", 0.62)) if brief.get("bake_scrim", True) else 0.0
        if bake:
            base_img = scrim(base_img, side, bake, (bx[0] * W, bx[1] * H, bx[2] * W, bx[3] * H))
        base_img.save(out, "JPEG", quality=92, optimize=True, subsampling=0)
        rep = {"platform": plat, "out": str(out), "background_only": True, "side": side, "accent": accent,
               "scrim_baked": bake, "type_box_frac": [round(v, 3) for v in bx],
               "type_box_px": [round(bx[0] * W), round(bx[1] * H), round(bx[2] * W), round(bx[3] * H)],
               "crop_in_source": [round(v) for v in crop], "upscale_factor": round(scale, 3),
               "warnings": warnings, "checks": file_checks(out, plat)}
        out.with_suffix(".report.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
        print(json.dumps(rep, indent=1))
        return

    g = geoms[side]
    hook_lines, px, f, stroke, tag = g["lines"], g["px"], g["font"], g["stroke"], g["tag"]
    box, band, align_right = g["box"], g["rect"], g["align_right"]

    # --- scrim: start light, darken until the hook background reaches the target contrast
    strength = float(brief.get("scrim", 0.45))
    body_band = (band[0], band[3] - g["body_h"], band[2], band[3])
    lum_bg = 1.0
    for _ in range(10):
        canvas = scrim(base_img, side, strength, band)
        region = np.asarray(canvas.crop(tuple(int(v) for v in body_band)), dtype=np.float32)
        lum_bg = float(np.percentile(srgb_lum(region), 85))
        if contrast(1.0, lum_bg) >= TARGET_CONTRAST or strength >= 0.90:
            break
        strength = min(0.90, strength + 0.06)
    ratio_white = contrast(1.0, lum_bg)

    def lum_of(hx):
        return float(srgb_lum(np.array(hex_rgb(hx), dtype=np.float32)))

    # highlighted word must read on the scrim; the tag keeps the frame's own accent
    hl_color = None
    if highlight:
        for c in (accent, "#FFD84A", "#4FE3FF"):
            if contrast(lum_of(c), lum_bg) >= 3.0:
                hl_color = hex_rgb(c)
                if c != accent:
                    warnings.append(f"accent {accent} too close to the background for the highlight; used {c}")
                break
        if hl_color is None:
            warnings.append("no accent colour reads on this background; highlight drawn in white")
    tag_bg = hex_rgb(accent)
    tag_fg = (10, 10, 10) if lum_of(accent) > 0.32 else (255, 255, 255)

    # --- draw: ink-aligned so right-aligned text lands exactly on the box edge
    x_left, x_right = band[0], band[2]
    y = band[1]
    shadow = Image.new("L", canvas.size, 0)
    sd = ImageDraw.Draw(shadow)
    drawn = []
    tag_rect = None
    if tag:
        tx0 = x_right - tag["w"] if align_right else x_left
        tag_rect = (tx0, y, tx0 + tag["w"], y + tag["h"])
        sd.rounded_rectangle([v + 3 for v in tag_rect], radius=round(tag["h"] * 0.22), fill=120)
        y += tag["h"] + tag["gap"]
    origins = []
    top0 = g["bbs"][0][1]
    off = max(3, px // 22)
    for k, (l, bb) in enumerate(zip(hook_lines, g["bbs"])):
        oy = y + stroke - top0 + k * px * lh
        ox = (x_right - stroke - bb[2]) if align_right else (x_left + stroke - bb[0])
        origins.append((ox, oy, l))
        sd.text((ox + off, oy + off), l, font=f, fill=170, stroke_width=stroke, stroke_fill=170)
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(3, px // 14)))
    canvas = Image.composite(Image.new("RGB", canvas.size, (0, 0, 0)), canvas, shadow)
    d = ImageDraw.Draw(canvas)
    if tag_rect:
        d.rounded_rectangle(tag_rect, radius=round(tag["h"] * 0.22), fill=tag_bg)
        eb, (pxp, pyp) = tag["bbox"], tag["pad"]
        d.text((tag_rect[0] + pxp - eb[0], tag_rect[1] + pyp - eb[1]), eyebrow, font=tag["font"], fill=tag_fg)
        drawn.append(tag_rect)
    hl_key = re.sub(r"\W", "", highlight)
    for ox, oy, line in origins:
        words = line.split(" ")
        cx = ox
        for wi, w in enumerate(words):
            seg = w + (" " if wi < len(words) - 1 else "")
            col = (hl_color or (255, 255, 255)) if hl_key and re.sub(r"\W", "", w.upper()) == hl_key \
                else (255, 255, 255)
            d.text((cx, oy), seg, font=f, fill=col, stroke_width=stroke, stroke_fill=(12, 12, 12))
            cx += f.getlength(seg)
        drawn.append(d.textbbox((ox, oy), line, font=f, stroke_width=stroke))
    tb = (min(b[0] for b in drawn), min(b[1] for b in drawn), max(b[2] for b in drawn), max(b[3] for b in drawn))

    # --- export JPEG under 2 MB (4:4:4 keeps type edges clean)
    q = 92
    while True:
        canvas.save(out, "JPEG", quality=q, optimize=True, progressive=True, subsampling=0 if q >= 85 else 2)
        if out.stat().st_size < MAX_BYTES or q <= 60:
            break
        q -= 5

    forbid_px = [(x0 * W, y0 * H, x1 * W, y1 * H) for x0, y0, x1, y1 in spec["forbid"]]
    cap = f.getbbox("H")[3] - f.getbbox("H")[1]
    checks = {**file_checks(out, plat),
              "type_inside_box": tb[0] >= box[0] - 1 and tb[1] >= box[1] - 1 and tb[2] <= box[2] + 1
                                 and tb[3] <= box[3] + 1,
              "type_clear_of_forbidden": not any(boxes_overlap(tb, z) for z in forbid_px),
              "hook_contrast_ge_3": ratio_white >= MIN_CONTRAST,
              "reads_at_phone_size": cap * tiny_scale >= MIN_CAP_AT_TINY,
              "real_frame_only": True}
    if ratio_white < TARGET_CONTRAST:
        warnings.append(f"hook contrast {ratio_white:.1f}:1 is below 4.5 (stroke + shadow carry it)")
    preview = out.with_name(out.stem + ".preview.jpg")
    preview_sheet(canvas, plat, preview, type_bbox=tb, type_box=box)
    report = {"platform": plat, "out": str(out), "preview": str(preview), "size": [W, H],
              "bytes": out.stat().st_size, "jpeg_quality": q, "source": src_desc,
              "source_size": list(frame.size), "crop_in_source": [round(v) for v in crop],
              "upscale_factor": round(scale, 3), "grade": brief.get("grade", "auto"), "side": side,
              "font": Path(resolve_font(style, " ".join(hook_lines))[0]).name, "font_px": px,
              "cap_px_at_phone": round(cap * tiny_scale, 1), "hook_lines": hook_lines, "eyebrow": eyebrow,
              "accent": accent, "accent_note": accent_note, "scrim": round(strength, 2),
              "hook_contrast": round(ratio_white, 2), **subj, "type_bbox": [round(v) for v in tb],
              "type_box": [round(v) for v in box], "checks": checks, "warnings": warnings,
              "pass": all(checks.values())}
    out.with_suffix(".report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("out", "preview", "size", "bytes", "upscale_factor", "side", "font",
                                             "font_px", "cap_px_at_phone", "hook_lines", "hook_contrast",
                                             "subject_under_type", "warnings", "pass")}, indent=1))
    if not report["pass"]:
        print(json.dumps({"failed": [k for k, v in checks.items() if not v]}))
        sys.exit(3)


def cmd_check(a: argparse.Namespace) -> None:
    p = Path(a.image).resolve()
    plat = ALIASES.get(a.platform.lower(), a.platform.lower())
    if plat not in PLATFORMS or not p.is_file():
        sys.exit("error: need an existing image and --platform youtube|shorts|reel|feed")
    checks = file_checks(p, plat)
    im = Image.open(p).convert("RGB")
    preview = p.with_name(p.stem + ".preview.jpg")
    if list(im.size) == list(PLATFORMS[plat]["size"]):
        preview_sheet(im, plat, preview)
    res = {"image": str(p), "platform": plat, "size": list(im.size), "bytes": p.stat().st_size,
           "checks": checks, "preview": str(preview) if preview.exists() else None, "pass": all(checks.values()),
           "note": "safe areas and legibility: look at the preview sheet"}
    print(json.dumps(res, indent=1))
    if not res["pass"]:
        sys.exit(3)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("analyze", help="probe, sample, rank, candidates, contact sheet, audio")
    p1.add_argument("video")
    p1.add_argument("--out", required=True)
    p1.add_argument("--samples", type=int, default=0, help="low-res samples to score (default 160, max 4 fps)")
    p1.add_argument("--candidates", type=int, default=8)
    p1.add_argument("--window", default="", help="only look inside START-END seconds, e.g. 14-20")
    p1.add_argument("--no-ocr", action="store_true", help="skip the burned-in text check")
    p1.add_argument("--dense", action="store_true", help="decode every sample even for heavy 4K/long input")
    p2 = sub.add_parser("render", help="render one cover from brief.json")
    p2.add_argument("brief")
    p3 = sub.add_parser("check", help="verify an exported cover (e.g. from Canva)")
    p3.add_argument("image")
    p3.add_argument("--platform", required=True)
    a = ap.parse_args()
    try:
        {"analyze": cmd_analyze, "render": cmd_render, "check": cmd_check}[a.cmd](a)
    except Refused as e:
        print(json.dumps({"refused": str(e)}, indent=1))
        sys.exit(2)


if __name__ == "__main__":
    main()
