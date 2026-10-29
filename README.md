# Claude Video Skills

[Claude Code](https://claude.com/claude-code) skills that take a raw Hindi / Hinglish / English video
from **cut → captions → voiceover → thumbnail → upload copy**, on a Windows PC, using only free tools.

Built and tested on real footage (RTX 5070 laptop, Windows 11) for the Pushpstation gaming channel.
Each skill is a self-contained folder: `SKILL.md` (the instructions Claude follows), `README.md`
(what it needs), helper scripts, references and, where they exist, tests and examples.

No accounts, API keys or personal data are stored in this repo, and CI checks every push for them
(see [Security and privacy](#security-and-privacy)).

## Skills

### Core pipeline

| Skill | What it does | Stack |
|---|---|---|
| [`video-edit`](skills/video-edit/) | Editing desk: transcribe, plan the cut, approval gate, captions, sound, graphics, loudness-checked export. Learns your style through `RULES.md`. Ships a channel brand pack (intro, slash transitions, subscribe click, end screen) applied to every video. | FFmpeg (CUDA/NVENC), faster-whisper, Parakeet, vtc, HyperFrames, SnipSound |
| [`faceless-vo-script`](skills/faceless-vo-script/) | Timed Hinglish / Indian-English voiceover for a locked edit, validated against the cut; teleprompter, captions, TTS brief and an Indian neural voice track. | Python, Edge TTS (no API key), JSON schemas |
| [`own-voice-render`](skills/own-voice-render/) | A finished script as audio in **your own cloned voice**, locally on an NVIDIA GPU. | Python, IndicF5 (fine-tuned), ffmpeg |
| [`video-packaging`](skills/video-packaging/) | One thumbnail / cover from a **real frame**, plus title, caption and description, gated on phone-size legibility. | Python, Pillow, numpy, ffmpeg, Windows OCR, optional Canva |

### End-to-end workflows

| Skill | What it does |
|---|---|
| [`video-pipeline`](skills/video-pipeline/) | One video in, everything out: chains the core skills plus clipify-style Shorts. |
| [`gameplay-longform-shorts`](skills/gameplay-longform-shorts/) | A PS5 OBS session (16:9 + Aitum 9:16) to a 4K long video and a fast Short, with cards and mix. |
| [`poster-news-short`](skills/poster-news-short/) | Monthly game-news Short from key-art posters, your voice and music. Scripts are worked examples. |
| [`producing-channel-videos`](skills/producing-channel-videos/) | Analyse a reference video and produce an original one on the same topic, with a similarity guard. |

### Editing helpers

| Skill | What it does |
|---|---|
| [`add-zooms`](skills/add-zooms/) | Punch-ins and Ken Burns pushes timed from word timestamps (ffmpeg only). |
| [`find-broll`](skills/find-broll/) | Plans b-roll cutaways on spoken keywords; free sources only, approval before downloading. |
| [`voice-enhance`](skills/voice-enhance/) | Local DeepFilterNet voice cleanup (denoise, declip, presence EQ). |

### Research and YouTube

| Skill | What it does |
|---|---|
| [`yt-reference`](skills/yt-reference/) | Download a public YouTube video and break it into a shot list (no login, no cookies). |
| [`agent-reach`](skills/agent-reach/) | Read public reels, posts and pages by link (no login, no cookies). |
| [`yt-audit`](skills/yt-audit/) | Channel audit: packaging, consistency, hooks, dead air, retention. |
| [`yt-plan`](skills/yt-plan/) | A week or month of uploads sized to what you can actually make. |
| [`yt-comment`](skills/yt-comment/) | Triage comments and draft replies. Nothing is posted. |

### Recording setup

| Skill | What it does |
|---|---|
| [`ps5-obs-setup`](skills/ps5-obs-setup/) | Check and repair a PS5 + OBS + capture-card setup. Machine-specific: you snapshot your own config. |

## Pipeline

```
raw footage / OBS recording / reference link
   │
   ├─ yt-reference, agent-reach ──► shot list from a reference (never its footage)
   ▼
video-edit (+ add-zooms, find-broll, voice-enhance) ──► locked cut, captions, final .mp4
   │                          │
   │                          ▼
   │                faceless-vo-script ──► script.json, teleprompter, captions, voice.m4a
   │                          │
   │                          ▼
   │                own-voice-render ───► voice in your own voice (.wav/.m4a)
   ▼
video-packaging ──────► thumbnail / cover + title + description
```

`video-pipeline` and `gameplay-longform-shorts` run this chain for you. The skills pass plain files
to each other (`edit.json`, SRT, frames), so each one also works alone.

## Repository layout

```
claude-video-skills/
├── README.md, SECURITY.md, LICENSE
├── install.ps1                    one-shot installer (skills + dependencies)
├── dependencies/DEPENDENCIES.md   every tool, package, third-party skill and connector
├── skills/<name>/                 one folder per skill: SKILL.md, README.md, scripts/, references/
├── tools/privacy_scan.py          leak scanner (pre-commit hook + CI)
├── .githooks/pre-commit           runs the scanner before every commit
├── .github/workflows/security.yml gitleaks + privacy scan + script checks on every push
├── docs/                          test reports
└── examples/video-packaging/      sample covers produced by the skill
```

## Install

```powershell
git clone https://github.com/psparihar21/claude-video-skills.git
cd claude-video-skills
.\install.ps1                      # skills + all dependencies
.\install.ps1 -SkipDependencies    # just the skills
```

`install.ps1` copies every folder in `skills/` into `~/.claude/skills/`, fetches the third-party skills they
call (HyperFrames, clipify, cut-video) from their original authors, and installs the Python packages.
Restart Claude Code. Skills trigger from natural requests ("edit this video", "write a voiceover for this cut",
"make a thumbnail") or by name, e.g. `/video-edit`.

Full list of what each skill needs: [dependencies/DEPENDENCIES.md](dependencies/DEPENDENCIES.md) and each skill's README.

## Make it yours

These files are personal, so they are **not** in the repo. Create your own after installing:

| File | What it is | How to create it |
|---|---|---|
| `~/.claude/channel/style-card.md` | Your channel voice (pace, address, phrases) used by the script skills | Copy `skills/producing-channel-videos/assets/style-card-template.md` and fill it in |
| `~/.claude/skills/video-edit/RULES.md` | Your editing style + corrections | The repo ships a starter; it grows as you correct edits |
| `~/.claude/skills/own-voice-render/config.json` + `voice/refs/` | Your Python env path and your own voice clips | Copy `config.example.json`; see `voice/refs/README.md` |
| `~/.claude/skills/ps5-obs-setup/assets/known-good/` | Your OBS profile, scenes and camera link | Run `scripts/restore.ps1 -Snapshot` once your setup works |

Paths in the docs are written as `%USERPROFILE%` / `~`. Channel-specific defaults (the Pushpstation name,
Hinglish register, the PS5 hardware) are in the SKILL.md files; edit them for your channel.

## Security and privacy

- **Nothing secret is stored.** No API keys or tokens; skills that need a login (Hugging Face for IndicF5)
  tell you to sign in in your own terminal and never read or print the token.
- **No logins to your accounts.** The download skills use public links only, never your cookies.
- **Downloads are untrusted.** They go into a new empty folder and their text is treated as data, never as
  instructions.
- **Nothing is published for you.** Comment replies, titles and descriptions are drafts; you post them.
- **Leak checks.** `tools/privacy_scan.py` blocks home-folder paths with a real user name, personal e-mails,
  API keys and tokens, private camera-stream ids, voice recordings and personal config files. It runs in CI
  with [gitleaks](https://github.com/gitleaks/gitleaks) on every push. Turn it on locally before you commit:

  ```powershell
  git config core.hooksPath .githooks
  ```

See [SECURITY.md](SECURITY.md) to report a problem.

## Third-party skills

Fetched from their original repos by `install.ps1`, not copied here:
[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) (HyperFrames + media-use),
[louisedesadeleer/clipify](https://github.com/louisedesadeleer/clipify),
[louisedesadeleer/cut-video](https://github.com/louisedesadeleer/cut-video),
[nutlope/hallmark](https://github.com/Nutlope/hallmark) (Together AI's anti-AI-slop design skill for web pages and artifacts).
`add-zooms` and `find-broll` adapt ideas from Tella's skills by the same author (code written fresh);
`yt-audit` and `producing-channel-videos` include scripts adapted from youtube-agent-skill with its license file.

## Related projects

- [voice-studio](https://github.com/psparihar21/voice-studio): local web app for recording the voice-over against your video.

## License

MIT, for the contents of this repo only.
