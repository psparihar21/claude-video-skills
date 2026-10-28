# Connectors and skills

Map each production step to whatever is actually enabled in this chat. Never assume a specific editor, voice vendor, stock site, or video model.

## How to inventory

1. Read the available skills list and the callable tool list. Deferred tools that can be loaded count as available; tools mentioned only in docs or memory do not.
2. For each step below, pick the best match. Prefer a dedicated tool over a general one (a stock-library connector over web search for footage).
3. Write `inventory.md`:

```
| Step | Tool | Status |
|---|---|---|
| Research | WebSearch | ok |
| Stock search | none | gap → search links + licence check list in handoff |
| Voice | none | gap → user records; script doc in handoff |
```

4. Refer to connector tools by fully qualified name, `ServerName:tool_name`, in the inventory and when calling them.

## Steps and what to look for

| Step | Look for | Fallback when missing |
|---|---|---|
| Research | Web search/fetch, research skill | Mark claims `[VERIFY]`, ask user for sources |
| User's channel (style only) | YouTube or channel analytics connector | Ask for 1–2 scripts or video transcripts |
| Transcription | Transcription skill or media tool | Ask user for a transcript or captions file |
| Image generation | Image-gen connector or design tool | Filming brief or stock |
| Video generation | Video-gen connector | Stock, still + motion graphic, or filming brief |
| Voice | TTS or voice connector | User records; give a read-along script with pace marks |
| Stock search | Stock or music library connector | Handoff list of searches + licence checks for the user |
| Music / SFX | Licensed music or SFX library connector | Ask for the user's licensed bed; list needed cues |
| Docs | Docs connector or document skill | Markdown files in the production folder |
| Captions | Caption skill or tool | SRT from the locked script with timecodes |
| Timeline export | Editor or composition skill/connector | Timeline notes in `handoff/` (row, file, in/out, track) |
| Thumbnail stills | Design or packaging skill | Thumbnail brief only |

## Known stack on the user's machine

Prefer these when step 0 confirms they are present. Verify every run: a skill must be in the available-skills list, a CLI or model must exist on disk. If one is missing, fall back to the table above.

| Step | Preferred tool | Notes |
|---|---|---|
| Voice, user's own | `own-voice-render` skill (IndicF5 clone, local GPU) | Hindi, Hinglish, English. No emotion control. Logged as `user-clone: own-voice-render`. |
| Voice, stock and emotive (English) | Qwen3-TTS CustomVoice in conda env `qwen3-tts` | Apache-2.0, local. Preset male and female voices; emotion and pace set by an instruction line per cue. Logged as `stock-tts: qwen3-tts <voice>`. |
| Voice, user's own with emotion (Hindi / Hinglish) | Chatterbox Multilingual + the user's LoRA `C:/voice/chatterbox/ft/epoch_4` (chosen by ear 2026-10-19) | MIT, local. Render with `C:/voice/chatterbox/render_own.py lines.json OUT_DIR` (moods calm / tense / excited). Text in Devanagari. Logged as `user-clone: chatterbox-lora-epoch4`. Reference must only ever be the user's own voice. |
| Voice, fallback | `faceless-vo-script` (Edge TTS, Indian English) or Kokoro via `media-use` | Free, little emotion. Edge TTS needs internet. |
| Hooks, titles, chapters, retention, niche outliers | `scripts/hookscore.py`, `title.py`, `chapters.py`, `retention.py`, `swipe.py` (from youtube-agent-skill, MIT) | Pure standard-library Python, no network. Any Python 3 works. |
| Reference analysis | `scripts/analyze_reference.py` run with `%APPDATA%/uv/tools/video-timeline-copilot/Scripts/python.exe -I` | That interpreter has faster-whisper with CUDA; the script adds the CUDA DLL folders itself. ffmpeg 9 is on PATH. |
| VO script timing | `faceless-vo-script` | Timed cues, emotion map, captions from the locked cut. |
| Edit and assembly | `video-edit` skill: FFmpeg + video-timeline-copilot | Primary editor. Follow its RULES.md. |
| Finishing in an NLE | DaVinci Resolve Free 21 (installed) | Free has no external scripting: hand off by FCPXML + SRT, the user imports it. |
| Motion graphics, cards | HyperFrames skills, local render only | Never cloud, lambda, or HeyGen TTS. |
| Shorts | `clipify` | 9:16 cut-downs from the finished video. |
| Tightening user recordings | `cut-video` | Silences, fillers, false starts. |
| Screen and game capture | OBS Studio (installed) | Filming briefs name OBS scenes when relevant. |
| Article / Instagram / X screenshots | Built-in browser or Claude in Chrome | Rules in `media-rights.md`, "Editorial screenshots". |
| Official gameplay and trailers | Publisher press-kit downloads; `yt-dlp` if installed | yt-dlp is not installed by default. Ask before installing. Rules in `media-rights.md`. |
| Music and SFX | SnipSound connector | Check and log each track's licence. |
| Thumbnail, title, description | `video-packaging` skill (Canva when connected) | Thumbnail from a real frame of the finished video. |
| Upload | The user | Never upload, schedule, or post. |

Qwen3-TTS CustomVoice, verified on this machine (2026-10-19): model `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`, interpreter `%USERPROFILE%/miniconda3/envs/qwen3-tts/python.exe -X utf8`, load with `dtype=torch.bfloat16, attn_implementation="sdpa"` (flash-attn is not installed), call `generate_custom_voice(text=..., language="English", speaker=..., instruct="<emotion and pace in plain English>")`. About 4.5 GB VRAM, about 1.2 s of compute per second of audio. Native-English voices are male only: `ryan` (dynamic), `aiden` (sunny American). Female options `serena` (warm) and `vivian` (bright) are Chinese-native voices speaking English.

Chatterbox, verified on this machine (2026-10-19): interpreter `C:/voice/chatterbox/.venv/Scripts/python.exe` with `PYTHONUTF8=1`; `ChatterboxMultilingualTTS.from_pretrained(device="cuda")`, `generate(text, language_id="hi", audio_prompt_path=..., exaggeration=..., cfg_weight=...)`; write with soundfile (torchaudio save needs torchcodec, not installed); write Hindi in Devanagari. About 3.9 GB VRAM, about 4–5 s per 6 s line. Speaker similarity to the user's real clips: Hindi 0.89–0.92 (real clips vs each other 0.925, IndicF5 clone 0.934); English 0.82, so keep English on `own-voice-render` or Ryan/Serena. Renders peak at 0 dBFS: loudnorm (TP −1.5) before mixing. The epoch-4 LoRA speaks a little faster than the user's natural pace and can clip final consonants of English loanwords ("round" → "राउन"): Whisper-check every line and re-seed or respell when it happens. Run the env with `setuptools<81` (perth needs pkg_resources). Outputs carry Resemble's inaudible Perth watermark.

**The user's stock voices (chosen 2026-10-19 after listening): `ryan` = male, `serena` = female.** Offer only these two unless the user asks for another. Still ask per video which one (male or female) and log it as `stock-tts: qwen3-tts ryan` or `stock-tts: qwen3-tts serena`, licence `apache-2.0`. Run Whisper on every render to confirm the words, and send clips to the user to listen to; you cannot hear them.

Free open-source tools or skills that would help may be proposed. Install one only after the user says yes to that download (name, source, size).

## Rules

- A tool that can only reach the reference is not a source for picture or sound. Use it for study only.
- Before any paid or quota-using call (generation, TTS, render), check the relevant approval gate.
- If a connector errors, record it in `inventory.md`, switch to the fallback, and tell the user in one line.
- Do not add API keys, tokens, or account details to any file. If a tool needs credentials, the user connects it outside the skill.
