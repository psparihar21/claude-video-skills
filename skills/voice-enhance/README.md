# voice-enhance

Free, offline voice cleanup with DeepFilterNet3: denoise, optional declip, high-pass, light presence EQ and compression.

## Requirements

ffmpeg, and DeepFilterNet in `~/.deepfilter-venv` (Python 3.11, CPU torch 2.1.2) - install steps are in `SKILL.md`.

## Scripts / usage

`uv run scripts/enhance.py IN.wav OUT.wav [--declip] [--pf] [--post none]`

The full workflow Claude follows is in [`SKILL.md`](SKILL.md).

## Privacy and safety

Runs locally; temporary copies of the voice are deleted after each run. Only for voices you have the right to use.
