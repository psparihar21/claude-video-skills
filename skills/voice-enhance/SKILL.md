---
name: voice-enhance
description: Clean up a recorded voice (the user's own takes, voiceovers) with free local AI denoising - removes room noise, hiss and fan, repairs clipped takes, adds light presence EQ and compression. Use when the voice sounds noisy, thin, harsh, clipped or quiet before it goes into an edit, a Short, or own-voice-render training clips. Not for loudness mixing (that happens in the final mix) and not for generating a voice.
---

# voice-enhance

Free, offline voice cleanup. Engine: **DeepFilterNet3** (needs `soundfile` as the torchaudio backend) (open source, Rikorose/DeepFilterNet), installed in `~/.deepfilter-venv` (Python 3.11, CPU torch 2.1.2; it needs no GPU and is fast).

## Use

```powershell
uv run "$env:USERPROFILE\.claude\skills\voice-enhance\scripts\enhance.py" IN.wav OUT.wav [--declip] [--pf] [--post none]
```

- `--declip`: the take hit 0 dBFS (check with `ffmpeg -i IN -af astats -f null -`, "Peak count" in the thousands). Repairs, then lowers 6 dB.
- `--pf`: stronger noise reduction; a little duller. Use only for very noisy rooms.
- `--post none`: skip the presence EQ and compression.
- Output is 48 kHz mono, not loudness-normalised. Level and ducking are done in the final mix (voice about -15 LUFS alone, music about -34 LUFS, final -14 LUFS).

## Rules
- Only the user's own voice (or voices they have the right to use). Run it on every take before splicing, level takes to each other after.
- Cleanup can make a voice sound slightly processed. If the user says it sounds robotic, rerun without `--pf`, or with `--post none`.
- You cannot hear audio: say so, and let the user listen.

## Install (if `~/.deepfilter-venv` is missing)
```powershell
uv venv $env:USERPROFILE\.deepfilter-venv --python <path to a Python 3.11 python.exe>
uv pip install --python $env:USERPROFILE\.deepfilter-venv\Scripts\python.exe "numpy<2" torch==2.1.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cpu
uv pip install --python $env:USERPROFILE\.deepfilter-venv\Scripts\python.exe deepfilternet soundfile
```
Newer torch/torchaudio break DeepFilterNet; keep 2.1.2 + Python 3.11 (on this PC uv's minor-version link fails, so pass the explicit python.exe path under `%LOCALAPPDATA%\uv\python`).
