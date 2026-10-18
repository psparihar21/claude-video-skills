# own-voice-render

A Claude skill that turns a finished script into an audio track **in your own cloned voice** (Hinglish, Hindi or English),
rendered locally on an NVIDIA GPU with a fine-tuned [IndicF5](https://huggingface.co/ai4bharat/IndicF5). No hosted or paid TTS.

```
03-script.json (faceless-vo-script) | SRT | JSON cues | .txt/.md
        │ ingest → draft → set-deva → lint
        ▼
Roman Hinglish → Devanagari (lexicon + your review) → IndicF5 render per cue
        ▼
fit cues to their time windows → loudness-normalise → .wav .m4a .srt + QA report
```

It is the "your own voice" step after `faceless-vo-script`, which writes the words.

## Files

| Path | Purpose |
|---|---|
| `SKILL.md` | Workflow and rules (Devanagari for Hindi *and* English cues, never handle the HF token, pronunciation is judged by the user) |
| `ovr.ps1` | Wrapper: runs `scripts/ovr.py` with the IndicF5 Python in UTF-8 mode |
| `scripts/ovr.py`, `core.py`, `engine.py`, `assemble.py` | CLI, text/timing logic, IndicF5 engine, audio assembly |
| `assets/lexicon.json` | Roman → Devanagari word lexicon |
| `references/` | Devanagari spelling rules, engine notes, input contract, QA, troubleshooting |
| `tests/test_core.py` | Unit tests for the core logic |
| `config.example.json` | Template for `config.json` (copy it; see below) |
| `voice/refs/` | **Your** reference clips. Not included (see below) |

## Setup (machine-specific, not in the repo)

1. NVIDIA GPU, a conda env with Python 3.10, torch (CUDA), `transformers==4.49.0` and IndicF5's dependencies, and ffmpeg.
2. Request access to the gated model `ai4bharat/IndicF5` on Hugging Face and run `hf auth login` in your own terminal.
3. Record 5-15 s clips of **your own voice** into `voice/refs/` as `<name>.wav` + `<name>.txt` (Devanagari transcript).
   Optionally fine-tune IndicF5 on more of your recordings and set `checkpoint`.
4. Copy `config.example.json` to `config.json` and set `python` (the env's `python.exe`), `checkpoint`, and your `refs`.
5. Check: `.\ovr.ps1 doctor` (see `SKILL.md` for the full command list).

## Voice data and consent

Reference clips, fine-tuned checkpoints and training data are personal biometric data and are intentionally **not published**
here (`voice/refs/*.wav`, `config.json` and `*.pt` are git-ignored). Only clone a voice you own or have written consent to use.