# faceless-vo-script

A Claude skill that writes a **timed voiceover** (Indian English or Hinglish) for a faceless video or faceless gameplay edit
that is already cut, then renders everything needed to record or generate the voice.

## Flow

```
edit.json / EDL / shot list / video
        │  (assets/edit-package.schema.json)
        ▼
01-beat-map.md ─► 03-script.json ──validate_script.py──► render_script.py
                                                           ├─ 02-script.md        teleprompter
                                                           ├─ 04-captions.srt
                                                           ├─ 05-record-notes.md
                                                           └─ 06-tts-brief.md     emotion map + engine settings
                                                      speak.py ─► 07-voice.m4a    Edge TTS, Indian voice, no API key
```

`03-script.json` is the single source of truth; every other file is a render of it.

## Files

| Path | Purpose |
|---|---|
| `SKILL.md` | Instructions and hard rules (no invented facts, no "hey guys" openers, locked cut is never re-edited) |
| `scripts/validate_script.py` | Checks lines against the cut: overlap, speaking rate, `[FACT]` placeholders |
| `scripts/render_script.py` | Produces teleprompter, captions, record notes, TTS brief |
| `scripts/speak.py` | Generates the voice track with Edge TTS (Indian English voices) |
| `scripts/sample_shots.py`, `catalog.py` | Frame sampling and voice catalog helpers |
| `references/` | Language register, formats, output contract, TTS settings, QA checklist, field notes |
| `assets/*.schema.json` | JSON schemas for the edit package and the script |
| `assets/examples/` | Two complete worked examples (`first-minute`, `ranked-push`) incl. generated `.m4a`, plus a `bad-overlap` failing fixture |
| `evals/triggers.json` | Should / should-not trigger prompts |
| `PASTE-INTO-CLAUDE.md`, `START-HERE.txt` | Using it in claude.ai (Project upload) instead of Claude Code |

## Requirements

Python 3.10+ and `pip install -r requirements.txt` (`edge-tts`). ffmpeg for audio post-processing. No paid APIs or keys.

## Quick check

```powershell
python scripts/validate_script.py --edit assets/examples/first-minute/edit.json --script assets/examples/first-minute/03-script.json   # Pass
python scripts/validate_script.py --edit assets/examples/bad-overlap/edit.json --script assets/examples/bad-overlap/03-script.json   # 8 errors (expected)
python scripts/validate_script.py --self-test
```