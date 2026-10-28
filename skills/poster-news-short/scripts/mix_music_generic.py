"""Edited music bed for the Short. uv run --with numpy mix_music.py <silent.mp4> <voice.wav> <timeline.json> <out.mp4>
Music = Night Runner (Dark), SnipSound id 317. The bed is automated by hand-made gain curve (not just a sidechain):
  intro swell, ducked while talking, a little extra dip on every game name, music lifts again in gaps and under the outro."""
import json, subprocess, sys
from pathlib import Path
import numpy as np

SIL, VOICE, TLJ, OUT = sys.argv[1:5]
J = (Path.home() / "Videos/pipeline/gta6-editions"); S = J / "scratch"
import os
MUS = Path(os.environ.get("MUSIC", J / "music" / "launch-day-energetic.mp3")); MSTART = float(os.environ.get("MSTART", "0"))
SR = 48000; HZ = 100
T = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SIL]))
BASE, TALK, NAME, OUTRO, INTRO = -19.0, -5.0, -2.5, +2.0, +3.0       # dB re. the bed's loudness in the gaps

def pcm(path, ch):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ar", str(SR), "-ac", str(ch), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, ch).copy()

# 1) bed at BASE loudness (loudnorm only measures the pre-edit loop, then the curve is applied)
base = S / "music_base.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(MSTART), "-t", f"{T:.2f}", "-i", str(MUS), "-af", f"aformat=channel_layouts=stereo,loudnorm=I={BASE}:TP=-4:LRA=7", "-ar", str(SR), str(base)], check=True)
m = pcm(base, 2); L = min(len(m), int(T * SR)); m = np.pad(m, ((0, max(0, int(T * SR) - len(m))), (0, 0)))[:int(T * SR)]

# 2) gain curve at 100 Hz
n = int(T * HZ) + 1; g = np.zeros(n)
v = pcm(VOICE, 1)[:, 0]; k = len(v) // 480; e = np.sqrt((v[:k * 480].reshape(k, 480) ** 2).mean(1) + 1e-12); db = 20 * np.log10(e)
talking = (db > np.percentile(db, 90) - 26).astype(float)
talking = np.convolve(talking, np.ones(12) / 12, "same") > 0.35          # bridge breaths, ignore blips
talking = np.pad(talking, (0, max(0, n - k)))[:n]
ev = json.load(open(TLJ))["events"]
g[talking] += TALK
for i, x in enumerate(ev):
    if x["scene"] == "poster":
        t0 = x["t"]; t1 = min(t0 + 1.5, ev[i + 1]["t"] if i + 1 < len(ev) else T)
        g[int(t0 * HZ):int(t1 * HZ)] += NAME * (talking[int(t0 * HZ):int(t1 * HZ)] > 0)
    if x["scene"] == "end": g[int(x["t"] * HZ):] += -TALK * 0.4 * (talking[int(x["t"] * HZ):] > 0) + OUTRO * 0   # outro: duck only 60 % as deep
g[:int(0.7 * HZ)] += INTRO * np.linspace(1, 0, int(0.7 * HZ))             # swell on the first frame, settles under the first word
# smooth: fast down (60 ms), slower up (350 ms)
sm = np.zeros(n); cur = g[0]
for i in range(n):
    a = 1 - np.exp(-1 / (HZ * (0.06 if g[i] < cur else 0.35))); cur += (g[i] - cur) * a; sm[i] = cur
gain = 10 ** (np.interp(np.arange(len(m)) / SR, np.arange(n) / HZ, sm) / 20).astype(np.float32)
m = m * gain[:, None]
# fades: in 0.12 s, out 1.4 s
fi, fo = int(0.12 * SR), int(1.4 * SR); m[:fi] *= np.linspace(0, 1, fi)[:, None]; m[L - fo:L] *= np.linspace(1, 0, fo)[:, None]; m[L:] = 0
env_wav = S / "music_env.wav"
import wave
with wave.open(str(env_wav), "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(m, -1, 1) * 32767).astype(np.int16).tobytes())

# 3) final mix: voice -15 LUFS (light compression) + edited bed, final -14 LUFS
mix = Path(OUT).with_suffix(".m4a")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(env_wav), "-i", VOICE, "-filter_complex",
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,acompressor=threshold=0.05:ratio=3:attack=5:release=150:makeup=3,loudnorm=I=-15:TP=-2:LRA=6,apad=whole_dur={T:.2f}[v];"
                f"[0:a][v]amix=inputs=2:normalize=0:duration=longest,alimiter=limit=0.75,loudnorm=I=-14:TP=-2.3:LRA=7[a]",
                "-map", "[a]", "-t", f"{T:.2f}", "-ar", "48000", "-c:a", "aac", "-b:a", "256k", str(mix)], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SIL, "-i", str(mix), "-map", "0:v", "-map", "1:a", "-c", "copy", "-t", f"{T:.2f}", "-movflags", "+faststart", OUT], check=True)
print("done", OUT, "| gain range dB", round(float(sm.min()), 1), "to", round(float(sm.max()), 1))
