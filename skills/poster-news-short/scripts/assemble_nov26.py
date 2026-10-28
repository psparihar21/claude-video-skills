"""Voice-take editor for the Nov 2026 Short. uv run --with numpy assemble_nov26.py
Take 4 up to the 'khel leje aur' pause, take 6 from 'Rapala' on. Both de-noised and levelled to each other,
every pause > 0.4 s squeezed to 0.25 s, leading/trailing silence trimmed, 25 ms cross-fades at every join.
Writes voice/final/voice.wav + timeline.json (scene start times taken from the words the user actually said)."""
import json, subprocess, sys
from pathlib import Path
import numpy as np

SR = 48000
REC = str(Path.home() / "voice-studio/recordings")
OUT = (Path.home() / "Videos/pipeline/ps-nov26/voice/final"); OUT.mkdir(parents=True, exist_ok=True)
TMP = (Path.home() / "Videos/pipeline/ps-nov26/scratch")
# (take, source start, source end): splice happens inside the pause after "khel leje aur" (take 4) / before "Rapala" (take 6)
PARTS = [(4, 0.0, 35.44), (6, 37.20, 57.60)]
KEEP, MINP, XF = 0.16, 0.28, 0.025

def clean(t):
    """voice-enhance skill output (DeepFilterNet + presence EQ; take 6 declipped): scratch/enh_tN.wav"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(TMP / f"enh_t{t}.wav"), "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def env(x):
    n = len(x) // 480; return np.sqrt((x[:n * 480].reshape(n, 480) ** 2).mean(1) + 1e-12)

def speech_rms(x):
    e = env(x); db = 20 * np.log10(e); act = db >= np.percentile(db, 8) + 12
    return float(np.sqrt((e[act] ** 2).mean())) if act.any() else 0.05

def runs_and_pauses(x):
    """voiced runs [(s,e)] in 10 ms frames, gaps < 0.10 s merged; adaptive threshold = noise floor + 7 dB"""
    db = 20 * np.log10(env(x)); v = db >= max(np.percentile(db, 8) + 7, np.percentile(db, 90) - 24); n = len(v); runs = []; i = 0
    while i < n:
        if v[i]:
            j = i
            while j < n and v[j]: j += 1
            runs.append([i / 100, j / 100]); i = j
        else: i += 1
    m = []
    for r in runs:
        if m and r[0] - m[-1][1] < 0.10: m[-1][1] = r[1]
        else: m.append(r)
    return m

def xfade_all(pieces):
    f = int(XF * SR); res = pieces[0]
    for p in pieces[1:]:
        if len(res) < f or len(p) < f: res = np.concatenate([res, p]); continue
        w = np.linspace(0, 1, f, dtype=np.float32); res = np.concatenate([res[:-f], res[-f:] * (1 - w) + p[:f] * w, p[f:]])
    return res

X = {t: clean(t) for t in {p[0] for p in PARTS}}
ref = speech_rms(X[4]); GAIN = {t: ref / speech_rms(X[t]) for t in X}
print("gain", {t: round(g, 2) for t, g in GAIN.items()})

pieces = []; maps = []   # maps: (take, src_s, src_e, out_s)
out_t = 0.0
for take, a, b in PARTS:
    x = X[take] * GAIN[take]
    runs = [r for r in runs_and_pauses(X[take]) if r[1] > a and r[0] < b]
    runs[0][0] = max(runs[0][0], a); runs[-1][1] = min(runs[-1][1], b)
    # a new piece starts only after a squeezed (> 0.4 s) pause; shorter pauses stay inside the piece untouched
    segs = []; cs = max(a, runs[0][0] - 0.10)
    for k, (s, e) in enumerate(runs):
        if k + 1 == len(runs): segs.append([cs, min(b, e + 0.14)])
        elif runs[k + 1][0] - e >= MINP:
            segs.append([cs, e + KEEP / 2]); cs = runs[k + 1][0] - KEEP / 2
    for s0, e0 in segs:
        pieces.append(x[int(s0 * SR):int(e0 * SR)]); maps.append((take, s0, e0, out_t)); out_t += (e0 - s0) - XF
voice = xfade_all(pieces)
peak = float(np.abs(voice).max()); voice = voice * (0.89 / peak) if peak > 0.89 else voice
raw = (voice * 32767).astype(np.int16)
import wave
with wave.open(str(OUT / "voice_raw.wav"), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(raw.tobytes())
dur = len(voice) / SR; print("voice", round(dur, 2), "s from", sum(p[2] - p[1] for p in maps) and round(sum(m[2] - m[1] for m in maps), 2), "s kept")

def out_time(take, t):
    for tk, s, e, o in maps:
        if tk == take and s - 1e-6 <= t <= e + 1e-6: return o + (t - s)
    # t fell in a removed pause: land on the next kept piece
    nxt = [m for m in maps if m[0] == take and m[1] > t]; return nxt[0][3] if nxt else dur

WORDS = {t: json.load(open(f"{REC}/_transcripts/full_t{t}/transcript.roman.json", encoding="utf8")) for t in (4, 6)}
def find(take, toks, after=0.0, before=1e9):
    w = WORDS[take]; low = [x["text"].lower().strip(".,") for x in w]
    for i in range(len(w) - len(toks) + 1):
        if w[i]["start"] >= after and w[i]["start"] <= before and all(low[i + j].startswith(toks[j]) for j in range(len(toks))): return w[i]["start"]
    raise SystemExit(f"not found {take} {toks}")
LEAD = 0.12
E = [("hook", None, 0.0),
 ("poster", "rdr2", out_time(4, find(4, ["red", "dead"]) - LEAD)),
 ("poster", "gta5", out_time(4, find(4, ["gta", "5"], 8.0) - LEAD)),
 ("pair", None, out_time(4, find(4, ["rockstar"]) - LEAD)),
 ("poster", "fm26", out_time(4, find(4, ["sports"]) - LEAD)),
 ("poster", "cricket24", out_time(4, find(4, ["cricket"]) - LEAD)),
 ("poster", "talos2", out_time(4, find(4, ["the", "talos"], 21.0) - LEAD)),
 ("poster", "rockofages3", out_time(4, find(4, ["rock", "of"]) - LEAD)),
 ("poster", "monsterboy", out_time(4, find(4, ["monster"]) - LEAD)),
 ("poster", "hotshot", out_time(4, find(4, ["hotshot"]) - LEAD)),
 ("poster", "edf41", out_time(4, find(4, ["earth"]) - LEAD)),
 ("poster", "thankgoodness", out_time(4, find(4, ["thank", "goodness"]) - LEAD)),
 ("poster", "rapala", out_time(6, find(6, ["rapla"], 36.0) - LEAD)),
 ("poster", "zombiedef", out_time(6, find(6, ["yet", "andar"]) - LEAD)),
 ("date", None, out_time(6, find(6, ["pleej"], 40.0) - LEAD)),
 ("end", None, out_time(6, find(6, ["video", "pasand"]) - LEAD))]
E = [{"scene": s, "key": k, "t": round(t, 3)} for s, k, t in E]
for a, b in zip(E, E[1:]): assert b["t"] > a["t"] + 0.5, (a, b)
(OUT / "timeline.json").write_text(json.dumps({"duration": round(dur, 3), "events": E, "map": [[m[0], round(m[1], 3), round(m[2], 3), round(m[3], 3)] for m in maps]}, indent=1))
for e in E: print(f"{e['t']:6.2f}  {e['scene']:7} {e['key'] or ''}")
