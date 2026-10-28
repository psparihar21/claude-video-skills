"""uv run --with numpy assemble_gta.py -> voice/final.wav + voice/anchors.json
Splices the user's takes (already denoised in voice/enh): hook t6, standard+pack t9, ultimate+shops t6, ending t17.
Cuts are moved to the quietest point inside a window (inside pauses), long pauses are squeezed, takes are levelled to each other."""
import json, wave
from pathlib import Path
import numpy as np
J = (Path.home() / "Videos/pipeline/gta6-editions/voice"); SR = 48000; FR = SR // 100  # 10 ms frames

def load(n):
    with wave.open(str(J / "enh" / f"t{n}.wav")) as w:
        assert w.getframerate() == SR and w.getnchannels() == 1
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
X = {n: load(n) for n in (6, 9, 17)}
def edb(x):
    k = len(x) // FR; return 10 * np.log10((x[:k * FR].reshape(k, FR) ** 2).mean(1) + 1e-12)
DB = {n: edb(x) for n, x in X.items()}
THR = {n: np.percentile(DB[n], 90) - 28 for n in X}

def quiet(n, lo, hi):
    """centre time of the quietest 30 ms inside [lo, hi]"""
    d = np.convolve(DB[n], np.ones(3) / 3, "same"); a, b = int(lo * 100), int(hi * 100); return (a + int(np.argmin(d[a:b]))) / 100 + 0.005

# (take, start, end); start/end are either a float (fixed) or (lo, hi) = pick the quietest point in that window
SEG = [
 (6, 0.09, (5.30, 5.95)),            # hook "Standard ya Ultimate ... GTA 6"
 (9, (5.20, 5.58), (22.65, 23.6)),   # indiya mein Standard ... Jason and Lucia ke liye free milenge
 (6, (21.00, 21.30), (38.45, 38.74)),  # a unique weapon pattern ... Ultimate 7499 ... raaid aauta kastams
 (6, (39.75, 39.96), (42.85, 43.14)),  # saara salon (second try), elektrik phaink taitoo pailar (fluent try)
 (17, (37.35, 37.64), None),         # yeh sab ismen extra hai ... subscribe, like, follow
]
GAP = [0.25, 0.10, 0.10, 0.10]  # silence inserted before segments 1..4
ANCH = [("std", 1, 5.60), ("pack", 1, 11.62), ("stanier", 1, 16.16), ("looks", 1, 19.32), ("wpat", 2, 21.44), ("ult", 2, 24.02), ("cheetah", 2, 29.54),
        ("rev", 2, 31.24), ("wyman", 2, 32.92), ("ride", 2, 37.78), ("sara", 3, 39.98), ("fang", 3, 41.52), ("catch", 4, 37.66), ("launch", 4, 41.62), ("end", 4, 43.08)]

out, maps, pos = [], [], 0.0  # maps[i] = list of (src_a, src_b, final_a)
TARGET = -21.0
for i, (n, a, b) in enumerate(SEG):
    a = quiet(n, *a) if isinstance(a, tuple) else a
    b = len(X[n]) / SR - 0.05 if b is None else (quiet(n, *b) if isinstance(b, tuple) else b)
    d = DB[n]; fa, fb = int(a * 100), int(b * 100); sil = d[fa:fb] < THR[n]
    # speech level of this segment -> gain to TARGET
    sp = d[fa:fb][~sil]; gain = min(TARGET - (10 * np.log10((10 ** (sp / 10)).mean())), 12.0); g = 10 ** (gain / 20)
    # keep intervals (frames): drop the middle of interior silences longer than 0.28 s down to 0.16 s; trim edge silence to 0.06 s
    keep, k = [], 0; N = fb - fa
    runs, s = [], None
    for j in range(N + 1):
        if j < N and sil[j]: s = j if s is None else s
        elif s is not None: runs.append((s, j)); s = None
    cut = []
    for (s, e) in runs:
        if s == 0: cut.append((0, max(0, e - 6)))
        elif e == N: cut.append((s + 6, N))
        elif e - s > 28: cut.append((s + 8, e - 8))
    pos_f = 0
    for (s, e) in cut:
        if s > pos_f: keep.append((pos_f, s))
        pos_f = max(pos_f, e)
    if pos_f < N: keep.append((pos_f, N))
    if i: pos += GAP[i - 1]; out.append(np.zeros(int(GAP[i - 1] * SR), np.float32))
    m = []
    for (s, e) in keep:
        ch = X[n][(fa + s) * FR:(fa + e) * FR] * g; f = min(240, len(ch) // 2); ch = ch.copy()
        ch[:f] *= np.linspace(0, 1, f); ch[-f:] *= np.linspace(1, 0, f)
        m.append(((fa + s) / 100, (fa + e) / 100, pos)); out.append(ch); pos += len(ch) / SR
    maps.append(m); print(f"seg{i} t{n} {a:.2f}-{b:.2f} gain {gain:+.1f} dB, kept {len(keep)} chunks")
y = np.concatenate(out + [np.zeros(int(0.5 * SR), np.float32)]); pk = np.abs(y).max()
if pk > 0.95: y *= 0.95 / pk
with wave.open(str(J / "final.wav"), "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((y * 32767).astype(np.int16).tobytes())
def fin(si, t):
    for (sa, sb, fa) in maps[si]:
        if sa <= t <= sb: return fa + (t - sa)
    sa, sb, fa = min(maps[si], key=lambda c: min(abs(t - c[0]), abs(t - c[1])))  # word fell in a squeezed pause: snap to the nearest kept edge
    return fa if t < sa else fa + (sb - sa)
A = {nm: round(fin(si, t), 3) for nm, si, t in ANCH}; A["dur"] = round(len(y) / SR, 3)
json.dump(A, open(J / "anchors.json", "w"), indent=1); print(A)
