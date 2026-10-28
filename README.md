# Claude Video Skills

Four core [Claude Code](https://claude.com/claude-code) skills that take a raw Hindi / Hinglish / English video
from **cut → captions → voiceover → thumbnail**, on a Windows PC, using only free tools.

Built and tested on real footage (RTX 5070 laptop, Windows 11). Each skill is a self-contained folder
with a `SKILL.md` (the instructions Claude follows), helper scripts, references and tests/examples.

| Skill | What it does | Stack |
|---|---|---|
| [`video-edit`](skills/video-edit/) | End-to-end editing desk: transcribe, plan the cut, approval gate, captions, sound, graphics, loudness-checked export. Learns your style through a `RULES.md` file. | FFmpeg (CUDA/NVENC), faster-whisper large-v3, Parakeet, vtc, HyperFrames, SnipSound |
| [`faceless-vo-script`](skills/faceless-vo-script/) | Writes a timed Hinglish / Indian-English voiceover for a locked edit, validates timing against the cut, renders teleprompter, captions, TTS brief and an Indian neural voice track. | Python, Edge TTS (no API key), JSON schemas |
| [`own-voice-render`](skills/own-voice-render/) | Turns a finished script into audio in **your own cloned voice** (Hinglish/Hindi/English), locally on an NVIDIA GPU: Roman-to-Devanagari conversion, cue fitting, loudness normalisation, QA report. | Python, IndicF5 (fine-tuned), ffmpeg |
| [`video-packaging`](skills/video-packaging/) | Builds one production-ready thumbnail / cover from a **real frame** of the video, plus title, caption and description. Skips frames with burned-in text, crops around the subject, gates on phone-size legibility. | Python, Pillow, numpy, ffmpeg, Windows OCR, optional Canva |

More skills built on top of these four:

| Skill | What it does |
|---|---|
| [`video-pipeline`](skills/video-pipeline/) | One video in, everything out: chains video-edit, clipify-style Shorts, voiceover and packaging. |
| [`gameplay-longform-shorts`](skills/gameplay-longform-shorts/) | A PS5 OBS session (16:9 + Aitum 9:16) to a 4K long video and a fast Short, with cards and mix. |
| [`poster-news-short`](skills/poster-news-short/) | Monthly news Short from key-art posters, own voice and music. Scripts are the worked examples. |
| [`add-zooms`](skills/add-zooms/) | Punch-ins and Ken Burns pushes on word timestamps (ffmpeg only). |
| [`find-broll`](skills/find-broll/) | Plans b-roll cutaways on spoken keywords, free sources only, approval before downloading. |
| [`voice-enhance`](skills/voice-enhance/) | Local DeepFilterNet voice cleanup (denoise, declip, presence EQ). |
| [`yt-reference`](skills/yt-reference/), [`agent-reach`](skills/agent-reach/) | Read a public YouTube video, reel or page by link (no logins, no cookies) and turn it into a shot list. |
| [`yt-audit`](skills/yt-audit/), [`yt-plan`](skills/yt-plan/), [`yt-comment`](skills/yt-comment/) | Hook, title and retention audit; video planning; comment replies (drafts only, nothing is posted). Scripts adapted from youtube-agent-skill, license file included. |
| [`ps5-obs-setup`](skills/ps5-obs-setup/) | Checks and repairs a PS5 + OBS recording setup. Machine-specific: run `restore.ps1 -Snapshot` to save your own known-good config (not shipped, it holds private device and camera-stream ids). |

## Pipeline

```
raw footage
   │
   ▼
video-edit ───────────► locked cut (edit.json / EDL, captions.srt, final .mp4)
   │                          │
   │                          ▼
   │                faceless-vo-script ──► script.json, teleprompter, captions, voice.m4a
   │                          │
   │                          ▼
   │                own-voice-render ───► voice in your own voice (.wav/.m4a)
   ▼
video-packaging ──────► thumbnail / cover + title + description
```

The skills pass plain files to each other (`edit.json`, SRT, frames), so each can also be used alone.

## Repository layout

```
claude-video-skills/
├── README.md
├── LICENSE
├── install.ps1                one-shot installer (skills + dependencies)
├── dependencies/DEPENDENCIES.md
├── skills/
│   ├── video-edit/            SKILL.md, RULES.md, scripts/
│   ├── faceless-vo-script/    SKILL.md, scripts/, references/, assets/ (schemas + examples), evals/
│   ├── own-voice-render/      SKILL.md, scripts/, references/, assets/lexicon.json, tests/ (no voice data)
│   └── video-packaging/       SKILL.md, scripts/, references/
├── docs/
│   └── video-packaging-v2-test-report.md   what broke on real footage and how v2 fixed it
└── examples/
    └── video-packaging/       sample covers produced by the skill
```

## Install

```powershell
git clone https://github.com/psparihar21/claude-video-skills.git
cd claude-video-skills
.\install.ps1                      # skills + all dependencies
.\install.ps1 -SkipDependencies    # just the skills (no dependencies)
```

`install.ps1` copies the skills into `~/.claude/skills/`, then fetches the third-party skills they call
(HyperFrames, clipify, cut-video) from their original authors, and installs the Python packages.
Restart Claude Code. Skills trigger from natural requests ("edit this video", "write a voiceover for this cut",
"make a thumbnail") or by name, e.g. `/video-edit`.

Full list of tools, packages, skills and connectors: [dependencies/DEPENDENCIES.md](dependencies/DEPENDENCIES.md).
Per-skill requirements are in each skill's README.

To use just one skill in another setup, copy its folder from `skills/` into that setup's skills directory; its README lists what it needs.

## Highlights (what to look at)

- **Approval gate + persistent style rules.** `video-edit` refuses to render the final cut until you say "yes" to a written
  `edit-decision.md`, and every correction you give is appended to `RULES.md` so the next video already follows it.
- **Hinglish pipeline.** GPU Whisper for Hindi speech, then word-by-word Devanagari → Roman romanizer that keeps timestamps,
  so captions come out as "yeh video dekho".
- **Validated voiceovers.** `faceless-vo-script` checks the script against the cut (overlap, speaking rate, unsourced facts)
  with JSON schemas and bad-input test fixtures before any audio is generated.
- **Measured thumbnails.** `video-packaging` gates on cap height at real phone tile width and WCAG-style contrast, and
  documents its own regression results in [`docs/`](docs/video-packaging-v2-test-report.md).

## Related projects

- [voice-studio](https://github.com/psparihar21/voice-studio): local web app for recording the voice-over against your video (feeds the voice-take editing step in `video-edit`).

## Dependencies

Third-party skills are fetched from their original repos by `install.ps1`, not copied here:
[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (HyperFrames + media-use),
[louisedesadeleer/clipify](https://github.com/louisedesadeleer/clipify),
[louisedesadeleer/cut-video](https://github.com/louisedesadeleer/cut-video).
See [dependencies/DEPENDENCIES.md](dependencies/DEPENDENCIES.md).

## License

MIT, for the contents of this repo only.
