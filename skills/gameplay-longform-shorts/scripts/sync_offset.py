"""Offset between two recordings of the same session (horizontal vs Aitum vertical).
usage: sync_offset.py a.wav b.wav   -> prints X where b_time = a_time + X (b started earlier => X > 0).
Use any mono wav; only the first 5 minutes are compared. Always confirm with one frame from each file."""
import sys, subprocess, numpy as np


def load(p, sr=8000, secs=300):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-t", str(secs), "-i", p, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).astype(float)
    return a - a.mean()


def offset(a, b, sr=8000):
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(b, n) * np.conj(np.fft.rfft(a, n)), n)
    k = int(np.argmax(c))
    return (k if k < n // 2 else k - n) / sr


if __name__ == "__main__":
    print(round(offset(load(sys.argv[1]), load(sys.argv[2])), 2))
