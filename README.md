# Claude Video Skills

Three [Claude Code](https://claude.com/claude-code) skills that take a raw Hindi / Hinglish / English video
from **cut â†’ captions â†’ voiceover â†’ thumbnail**, on a Windows PC, using only free tools.

Built and tested on real footage (RTX 5070 laptop, Windows 11). Each skill is a self-contained folder
with a `SKILL.md` (the instructions Claude follows), helper scripts, references and tests/examples.

| Skill | What it does | Stack |
|---|---|---|
| [`video-edit`](skills/video-edit/) | End-to-end editing desk: transcribe, plan the cut, approval gate, captions, sound, graphics, loudness-checked export. Learns your style through a `RULES.md` file. | FFmpeg (CUDA/NVENC), faster-whisper large-v3, Parakeet, vtc, HyperFrames, SnipSound |
| [`faceless-vo-script`](skills/faceless-vo-script/) | Writes a timed Hinglish / Indian-English voiceover for a locked edit, validates timing against the cut, renders teleprompter, captions, TTS brief and an Indian neural voice track. | Python, Edge TTS (no API key), JSON schemas |
| [`video-packaging`](skills/video-packaging/) | Builds one production-ready thumbnail / cover from a **real frame** of the video, plus title, caption and description. Skips frames with burned-in text, crops around the subject, gates on phone-size legibility. | Python, Pillow, numpy, ffmpeg, Windows OCR, optional Canva |

## Pipeline

```
raw footage
   â”‚
   â–¼
video-edit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–º locked cut (edit.json / EDL, captions.srt, final .mp4)
   â”‚                          â”‚
   â”‚                          â–¼
   â”‚                faceless-vo-script â”€â”€â–º script.json, teleprompter, captions, voice.m4a
   â–¼
video-packaging â”€â”€â”€â”€â”€â”€â–º thumbnail / cover + title + description
```

The skills pass plain files to each other (`edit.json`, SRT, frames), so each can also be used alone.

## Repository layout

```
claude-video-skills/
â”œâ”€â”€ README.md
â”œâ”€â”€ LICENSE
â”œâ”€â”€ install.ps1                one-shot installer (skills + dependencies)
â”œâ”€â”€ dependencies/DEPENDENCIES.md
â”œâ”€â”€ skills/
â”‚   â”œâ”€â”€ video-edit/            SKILL.md, RULES.md, scripts/
â”‚   â”œâ”€â”€ faceless-vo-script/    SKILL.md, scripts/, references/, assets/ (schemas + examples), evals/
â”‚   â””â”€â”€ video-packaging/       SKILL.md, scripts/, references/
â”œâ”€â”€ docs/
â”‚   â””â”€â”€ video-packaging-v2-test-report.md   what broke on real footage and how v2 fixed it
â””â”€â”€ examples/
    â””â”€â”€ video-packaging/       sample covers produced by the skill
```

## Install

```powershell
git clone https://github.com/psparihar21/claude-video-skills.git
cd claude-video-skills
.\install.ps1                      # skills + all dependencies
.\install.ps1 -SkipDependencies    # just the three skills
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
- **Hinglish pipeline.** GPU Whisper for Hindi speech, then word-by-word Devanagari â†’ Roman romanizer that keeps timestamps,
  so captions come out as "yeh video dekho".
- **Validated voiceovers.** `faceless-vo-script` checks the script against the cut (overlap, speaking rate, unsourced facts)
  with JSON schemas and bad-input test fixtures before any audio is generated.
- **Measured thumbnails.** `video-packaging` gates on cap height at real phone tile width and WCAG-style contrast, and
  documents its own regression results in [`docs/`](docs/video-packaging-v2-test-report.md).

## Dependencies

Third-party skills are fetched from their original repos by `install.ps1`, not copied here:
[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (HyperFrames + media-use),
[louisedesadeleer/clipify](https://github.com/louisedesadeleer/clipify),
[louisedesadeleer/cut-video](https://github.com/louisedesadeleer/cut-video).
See [dependencies/DEPENDENCIES.md](dependencies/DEPENDENCIES.md).

## License

MIT, for the contents of this repo only.
