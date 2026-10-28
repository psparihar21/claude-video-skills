"""Clean a spoken-voice recording: (optional declip) -> high-pass -> DeepFilterNet denoise -> gentle presence EQ + compression.
uv run enhance.py IN.wav OUT.wav [--declip] [--pf] [--post none]
Free and local. DeepFilterNet lives in ~/.deepfilter-venv (CPU torch 2.1.2, no GPU needed). Output: 48 kHz mono 16-bit wav, NOT loudness-normalised."""
import argparse, os, subprocess, sys, tempfile
from pathlib import Path

DF = Path.home() / ".deepfilter-venv" / "Scripts" / "deepFilter.exe"
a = argparse.ArgumentParser(); a.add_argument("inp"); a.add_argument("out")
a.add_argument("--declip", action="store_true", help="repair clipped peaks first (recording was too hot)")
a.add_argument("--pf", action="store_true", help="DeepFilterNet post-filter: stronger noise cut, slightly duller")
a.add_argument("--post", default="voice", choices=["voice", "none"], help="voice = presence EQ + light compression")
a = a.parse_args()
if not DF.exists(): sys.exit(f"DeepFilterNet missing: {DF}. See SKILL.md install steps.")
# temp copies of the user's voice are deleted even when a step fails
with tempfile.TemporaryDirectory(prefix="enh_") as td:
    tmp = Path(td); pre = tmp / "pre.wav"
    pre_af = ("adeclip=w=55:o=75:a=8:t=10:n=1000," if a.declip else "") + "highpass=f=75" + (",volume=-6dB" if a.declip else "")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.inp, "-af", pre_af, "-ar", "48000", "-ac", "1", str(pre)], check=True)
    subprocess.run([str(DF), *(["--pf"] if a.pf else []), "--output-dir", str(tmp / "o"), str(pre)], check=True, env={**os.environ, "PYTHONWARNINGS": "ignore"}, stdout=subprocess.DEVNULL)
    den = next((tmp / "o").glob("*.wav"))
    post = "equalizer=f=3200:t=q:w=1.0:g=2,equalizer=f=180:t=q:w=1.0:g=1,acompressor=threshold=0.06:ratio=2.5:attack=6:release=160:makeup=2" if a.post == "voice" else "anull"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(den), "-af", post, "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", a.out], check=True)
print("enhanced ->", a.out)
