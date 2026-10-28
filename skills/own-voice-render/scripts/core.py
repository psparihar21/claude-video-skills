"""Shared, GPU-free logic for own-voice-render: config, text, ingest, lint, QA, timing.

Everything here is pure so it can be unit-tested (tests/test_core.py) without a GPU.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import shutil
import unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ENGINE_VERSION = "1"
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
LATIN = re.compile(r"[A-Za-z]")
DIGIT = re.compile(r"[0-9०-९]")
ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"), None)
PUNCT_MAP = {
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "–": ", ", "—": ", ", "…": "...", " ": " ",
}
SENT_END = re.compile(r"(?<=[।?!.])\s+")


# --------------------------------------------------------------------------- config
def _abs(p: str) -> str:
    if not p:
        return p
    q = Path(p)
    return str(q if q.is_absolute() else (SKILL / q))


def load_config() -> dict:
    path = SKILL / "config.json"
    if not path.exists():  # fresh clone: config.json is personal and gitignored
        path = SKILL / "config.example.json"
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for ref in cfg["refs"].values():
        ref["audio"] = _abs(ref["audio"])
        ref["text_file"] = _abs(ref["text_file"])
    return cfg


def ref_text(ref: dict) -> str:
    return Path(ref["text_file"]).read_text(encoding="utf-8").strip()


def load_lexicon() -> dict:
    lex = json.loads((SKILL / "assets" / "lexicon.json").read_text(encoding="utf-8"))
    for k in ("hindi", "loanwords"):
        lex[k] = {w.lower(): d for w, d in lex[k].items() if not w.endswith("_")}
    return lex


def find_ffmpeg(cfg: dict | None = None) -> str:
    if cfg and cfg.get("ffmpeg") and Path(cfg["ffmpeg"]).exists():
        return cfg["ffmpeg"]
    found = shutil.which("ffmpeg")
    if found:
        return found
    base = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    hits = glob.glob(os.path.join(base, "Gyan.FFmpeg*", "**", "bin", "ffmpeg.exe"), recursive=True)
    if hits:
        return hits[0]
    raise SystemExit("ffmpeg not found. Install it: winget install Gyan.FFmpeg")


def find_vocab() -> Path | None:
    base = Path.home() / ".cache" / "huggingface" / "hub" / "models--ai4bharat--IndicF5" / "snapshots"
    hits = sorted(base.glob("*/checkpoints/vocab.txt")) if base.exists() else []
    return hits[-1] if hits else None


def load_vocab() -> set[str]:
    v = find_vocab()
    if not v:
        return set()
    return {line.rstrip("\n") for line in v.read_text(encoding="utf-8").split("\n")} | {" "}


# --------------------------------------------------------------------------- text
def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s).translate(ZERO_WIDTH)
    for a, b in PUNCT_MAP.items():
        s = s.replace(a, b)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.!?।])", r"\1", s)
    return s.strip()


def has_devanagari(s: str) -> bool:
    return bool(DEVANAGARI.search(s))


def speech_chars(s: str) -> int:
    """Characters that carry speech (letters and combining marks). Used for rate QA and calibration."""
    return sum(1 for c in s if unicodedata.category(c)[0] in ("L", "M"))


def split_sentences(text: str) -> list[str]:
    parts = [p.strip() for p in SENT_END.split(text) if p.strip()]
    out: list[str] = []
    for p in parts:
        if out and speech_chars(p) < 8:
            out[-1] += " " + p
        else:
            out.append(p)
    return out


def split_long(sentence: str, max_chars: int) -> list[str]:
    """Split an over-long sentence at clause boundaries, never inside a word."""
    if len(sentence) <= max_chars:
        return [sentence]
    pieces = re.split(r"(?<=[,;:])\s+", sentence)
    out, cur = [], ""
    for p in pieces:
        if cur and len(cur) + 1 + len(p) > max_chars:
            out.append(cur)
            cur = p
        else:
            cur = (cur + " " + p).strip()
    if cur:
        out.append(cur)
    final: list[str] = []
    for o in out:  # last resort: split on spaces
        while len(o) > max_chars:
            cut = o.rfind(" ", 0, max_chars)
            cut = cut if cut > 20 else max_chars
            final.append(o[:cut].strip())
            o = o[cut:].strip()
        if o:
            final.append(o)
    return final


def chunks_for(text: str, max_chars: int) -> list[str]:
    """Sentences -> chunks, each ending in sentence punctuation (the model needs it to stop cleanly)."""
    chunks: list[str] = []
    for s in split_sentences(normalize_text(text)):
        for piece in split_long(s, max_chars):
            if not re.search(r"[।?!.]$", piece):
                piece = piece.rstrip(",;:") + ("।" if has_devanagari(piece) else ".")
            chunks.append(piece)
    return chunks


def sha(*parts: str | bytes) -> str:
    h = hashlib.sha1()
    for p in parts:
        h.update(p if isinstance(p, bytes) else p.encode("utf-8"))
        h.update(b"\x1f")
    return h.hexdigest()[:16]


# --------------------------------------------------------------------------- draft (roman -> devanagari)
WORD = re.compile(r"[A-Za-z]+(?:'[a-z]+)?|[^A-Za-z]+")


def draft_devanagari(roman: str, lex: dict, overrides: dict | None = None) -> tuple[str, list[str]]:
    """Convert known Roman words; wrap anything else in [[ ]] for the agent to resolve. Returns (text, unknown)."""
    over = {k.lower(): v for k, v in (overrides or {}).items()}
    amb = set(lex["ambiguous"])
    keep = set(lex["keep_latin"])
    out, unknown = [], []
    for tok in WORD.findall(roman):
        if not LATIN.match(tok):
            out.append(tok)
            continue
        w = tok.lower()
        if tok in keep:
            out.append(tok)
        elif w in over:
            out.append(over[w])
        elif w in lex["loanwords"]:
            out.append(lex["loanwords"][w])
        elif w in lex["hindi"] and w not in amb:
            out.append(lex["hindi"][w])
        else:
            out.append(f"[[{tok}]]")
            unknown.append(tok)
    text = "".join(out)
    text = text.replace(" .", ".")
    text = re.sub(r"\.(\s|$)", "।\\1", text)
    return text, unknown


def hindi_ratio(text: str, lex: dict) -> float:
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", text)]
    if not words:
        return 0.0
    hits = sum(1 for w in words if w in lex["hindi"] and w not in set(lex["ambiguous"]))
    return hits / len(words)


# --------------------------------------------------------------------------- lint
def lint_text(text: str, lang: str, vocab: set[str], lex: dict, max_chunk: int = 150) -> list[dict]:
    """Return findings: {level: error|warn, code, msg}. `lang` is hi (Devanagari expected) or en (Latin)."""
    f: list[dict] = []

    def add(level: str, code: str, msg: str):
        f.append({"level": level, "code": code, "msg": msg})

    if not text.strip():
        add("error", "empty", "cue has no text")
        return f
    if "[[" in text or "]]" in text:
        add("error", "unresolved", "unresolved [[word]] markers: " + ", ".join(re.findall(r"\[\[(.*?)\]\]", text)))
    if "[FACT:" in text:
        add("error", "fact-hole", "[FACT: ...] hole: the script is not final")
    if DIGIT.search(text):
        add("error", "digits", "digits in text: spell numbers out in words (the model mispronounces numerals)")
    if lang == "hi":
        stripped = text
        for k in lex["keep_latin"]:
            stripped = stripped.replace(k, "")
        latin = re.findall(r"[A-Za-z]+", stripped)
        if latin:
            add("error", "latin-in-hindi", "Latin words in a Hindi cue (write them in Devanagari): " + ", ".join(sorted(set(latin))))
        if not has_devanagari(text):
            add("error", "no-devanagari", "language is hi but the text has no Devanagari")
        for bad, good in lex["avoid"].items():
            if bad in text:
                add("warn", "avoid-spelling", f"'{bad}' sounds wrong; approved spelling is '{good}'")
    else:
        if has_devanagari(text):
            add("warn", "devanagari-in-en", "Devanagari inside an English cue: set the cue language to hi if it is Hindi")
    if vocab:
        miss = sorted({c for c in text if c not in vocab and not c.isspace()})
        if miss:
            add("error", "not-in-vocab", "characters the model has never seen: " + " ".join(f"{c}(U+{ord(c):04X})" for c in miss))
    for ch in chunks_for(text, max_chunk):
        if len(ch) > max_chunk + 40:
            add("warn", "long-chunk", f"chunk of {len(ch)} chars may drift: {ch[:40]}...")
    if re.search(r"(.)\1{3,}", text):
        add("warn", "repeat", "a character repeats 4+ times; the model may stutter")
    return f


# --------------------------------------------------------------------------- ingest
SRT_TIME = re.compile(r"(\d+):(\d\d):(\d\d)[,.](\d{1,3})\s*-->\s*(\d+):(\d\d):(\d\d)[,.](\d{1,3})")


def _t(h, m, s, ms) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def parse_srt(text: str) -> list[dict]:
    cues, blocks = [], re.split(r"\n\s*\n", text.replace("\r\n", "\n").strip())
    for b in blocks:
        lines = [l for l in b.split("\n") if l.strip()]
        for i, l in enumerate(lines):
            m = SRT_TIME.search(l)
            if m:
                g = m.groups()
                body = " ".join(lines[i + 1:]).strip()
                if body:
                    cues.append({"in_sec": _t(*g[:4]), "out_sec": _t(*g[4:]), "text": re.sub(r"<[^>]+>", "", body)})
                break
    return cues


def strip_markdown(text: str) -> list[list[str]]:
    """Markdown/plain text -> paragraphs (list of sentences lists is built later). Drops headings, code, tables, notes."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    paras, cur = [], []
    for line in text.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if not s:
            if cur:
                paras.append(" ".join(cur)); cur = []
            continue
        if s.startswith("#") or s.startswith("|") or re.match(r"^[-*_]{3,}$", s):
            continue
        s = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", s)
        s = re.sub(r"^\s*>\s*", "", s)
        s = re.sub(r"\[(?:\d+:)?\d+:\d\d(?:\.\d+)?\]", "", s)           # [00:12] timestamps
        s = re.sub(r"^\(?(?:stage|note|sfx|music|b-?roll)\b[^)]*\)?:?.*$", "", s, flags=re.I) if re.match(r"^\(", s) else s
        s = re.sub(r"[*_`~]+", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        if s.strip():
            cur.append(s.strip())
    if cur:
        paras.append(" ".join(cur))
    return [[p] for p in paras]


def ingest_file(path: Path, lang_hint: str = "auto", lex: dict | None = None, english_mode: str = "devanagari") -> dict:
    """Normalize any supported script into a plan. Never invents timing."""
    lex = lex or load_lexicon()
    raw = path.read_text(encoding="utf-8-sig")
    kind = path.suffix.lower().lstrip(".")
    plan: dict = {"source": {"path": str(path), "kind": kind}, "mode": "sequential", "cues": [],
                  "video_duration_sec": None, "pronounce": {}, "warnings": [], "ignored": []}

    def lang_of(text: str, register: str | None = None) -> str:
        if lang_hint in ("hi", "en"):
            return lang_hint
        if register == "hinglish":
            return "hi"
        if register == "indian-english":
            return "en"
        if has_devanagari(text):
            return "hi"
        return "hi" if hindi_ratio(text, lex) >= 0.15 else "en"

    plan["english_mode"] = english_mode

    def add(text: str, lang: str, **extra):
        from_en = False
        if lang == "en" and english_mode == "devanagari" and not has_devanagari(text):
            lang, from_en = "hi", True   # English is read through the Hindi path: Devanagari text, Hindi reference
        cue = {"id": f"c{len(plan['cues']) + 1:02d}", "lang": lang, "roman": text, "deva": "", "seed": None,
               "ref": None, "in_sec": None, "out_sec": None, "paragraph_break": False, "from_english": from_en}
        cue.update(extra)
        if lang == "en" or has_devanagari(text):
            cue["deva"] = normalize_text(text)
        plan["cues"].append(cue)

    if kind == "json":
        data = json.loads(raw)
        if isinstance(data, dict) and "cues" in data and data.get("cues") and "spoken" in data["cues"][0]:
            # faceless-vo-script 03-script.json
            plan["mode"] = "timed"
            plan["slug"] = data.get("slug")
            plan["title"] = data.get("title")
            plan["status"] = data.get("status")
            plan["video_duration_sec"] = data.get("video_duration_sec")
            plan["intentional_silence"] = data.get("intentional_silence", [])
            plan["source"]["format"] = "faceless-vo-script"
            for p in data.get("pronounce", []):
                plan["pronounce"][p["word"]] = p["say"]
            if data.get("status") == "draft":
                plan["warnings"].append("source status is 'draft': cues may contain [FACT:] holes and are not final")
            for c in data["cues"]:
                lang = lang_of(c["spoken"], data.get("register"))
                add(c["spoken"], lang, id=c["id"], in_sec=float(c["in_sec"]), out_sec=float(c["out_sec"]),
                    shot_id=c.get("shot_id"), role=c.get("role"))
                for p in c.get("pronounce", []):
                    plan["pronounce"][p["word"]] = p["say"]
                if c.get("performance") or c.get("emphasis"):
                    plan["ignored"].append(c["id"])
        else:
            items = data["cues"] if isinstance(data, dict) and "cues" in data else data
            if isinstance(items, dict):
                items = [items]
            for i, c in enumerate(items):
                if isinstance(c, str):
                    c = {"text": c}
                text = c.get("text") or c.get("spoken") or c.get("line") or ""
                kw = {}
                s, e = c.get("in_sec", c.get("start")), c.get("out_sec", c.get("end"))
                if s is not None and e is not None:
                    kw = {"in_sec": float(s), "out_sec": float(e)}
                    plan["mode"] = "timed"
                if c.get("id"):
                    kw["id"] = str(c["id"])
                add(text, lang_of(text, c.get("register")), **kw)
    elif kind == "srt":
        plan["mode"] = "timed"
        for c in parse_srt(raw):
            add(c["text"], lang_of(c["text"]), in_sec=c["in_sec"], out_sec=c["out_sec"])
    else:  # txt, md, anything else
        for para in strip_markdown(raw):
            for i, text in enumerate(split_sentences(normalize_text(para[0]))):
                add(text, lang_of(text), paragraph_break=(i == 0 and bool(plan["cues"])))
    if not plan["cues"]:
        raise SystemExit(f"no speakable text found in {path}")
    ids = [c["id"] for c in plan["cues"]]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate cue ids in the source script")
    if plan["mode"] == "timed":
        prev = 0.0
        for c in plan["cues"]:
            if c["out_sec"] <= c["in_sec"]:
                raise SystemExit(f"cue {c['id']}: out_sec <= in_sec")
            if c["in_sec"] < prev - 1e-6:
                plan["warnings"].append(f"cue {c['id']} starts before the previous cue ends; windows will be clipped")
            prev = c["out_sec"]
    return plan


# --------------------------------------------------------------------------- audio QA (numpy only)
def audio_metrics(x, sr: int, floor_db: float = -45.0) -> dict:
    import numpy as np

    x = np.asarray(x, dtype="float32")
    if x.size == 0 or not np.isfinite(x).all():
        return {"ok": False, "peak": 0.0, "rms_db": -120.0, "lead_sil": 0.0, "tail_sil": 0.0, "duration": 0.0, "finite": False}
    win = max(1, int(0.02 * sr))
    n = x.size // win
    frames = x[: n * win].reshape(n, win)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    live = np.where(db > floor_db)[0]
    lead = float(live[0] * win / sr) if live.size else float(x.size / sr)
    tail = float((n - 1 - live[-1]) * win / sr) if live.size else float(x.size / sr)
    return {"ok": True, "finite": True, "peak": float(np.abs(x).max()),
            "rms_db": float(20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)),
            "lead_sil": lead, "tail_sil": tail, "duration": float(x.size / sr),
            "live_ratio": float(live.size / max(n, 1))}


def trim_edges(x, sr: int, floor_db: float, keep: float):
    import numpy as np

    m = audio_metrics(x, sr, floor_db)
    if not m["ok"] or m["live_ratio"] == 0:
        return x
    start = max(0, int((m["lead_sil"] - keep) * sr))
    end = len(x) - max(0, int((m["tail_sil"] - keep) * sr))
    return np.asarray(x[start:end], dtype="float32")


def qa_chunk(text: str, x, sr: int, lang: str, cfg: dict) -> list[str]:
    """Return failure codes. Mispronunciation cannot be detected here: a human listens (candidates/lock)."""
    m = audio_metrics(x, sr, cfg["silence_floor_db"])
    flags: list[str] = []
    if not m["ok"]:
        return ["non-finite-or-empty"]
    if m["peak"] >= 0.995:
        flags.append("clipping")
    if m["rms_db"] < -40:
        flags.append("near-silent")
    if m["live_ratio"] < 0.35:
        flags.append("mostly-silence")
    st = cfg["rate_stats"].get(lang, {})
    if st.get("median"):
        live_dur = max(m["duration"] - m["lead_sil"] - m["tail_sil"], 0.05)
        cps = speech_chars(text) / live_dur
        if cps > st["hi"]:
            flags.append(f"too-fast({cps:.1f}cps)")
        elif cps < st["lo"]:
            flags.append(f"too-slow({cps:.1f}cps)")
    return flags


# --------------------------------------------------------------------------- timing
def plan_fit(spoken: float, window: float, tempo_cap: float, margin: float = 0.04) -> dict:
    """How a rendered cue fits its window. Never speeds up beyond tempo_cap; never silently truncates."""
    room = max(0.3, window - margin)
    if spoken <= room:
        return {"tempo": 1.0, "status": "fits", "final": spoken}
    need = spoken / room
    if need <= tempo_cap:
        return {"tempo": round(need, 4), "status": "sped", "final": room}
    return {"tempo": tempo_cap, "status": "overflow", "final": spoken / tempo_cap, "over_by": round(spoken / tempo_cap - room, 3)}


def fmt_srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def load_locks(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def lock_key(text: str, lang: str) -> str:
    return sha(normalize_text(text), lang)
