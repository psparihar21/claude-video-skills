# Dependencies

Everything the skills need, so they work on a fresh machine. Third-party items are **not copied into this repo**;
`install.ps1` fetches them from their original authors, who own them and set their licenses.

## Third-party Claude skills

| Skill(s) | Used by | Source | Install |
|---|---|---|---|
| `hyperframes`, `hyperframes-core`, `-animation`, `-audio`, `-cli`, `-creative`, `-keyframes`, `-registry`, `-studio`, `media-use` | `video-edit` (titles, lower thirds, local transcription) | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | `npx skills add heygen-com/hyperframes -g -y` |
| `clipify` | `video-edit` (Shorts method) | [louisedesadeleer/clipify](https://github.com/louisedesadeleer/clipify) (MIT) | `git clone` into `~/.claude/skills/clipify` |
| `cut-video` | `video-edit` (cutting method) | [louisedesadeleer/cut-video](https://github.com/louisedesadeleer/cut-video) (MIT) | `git clone` into `~/.claude/skills/cut-video` |

`video-edit` uses `clipify` and `cut-video` as method references only. It translates their macOS commands to Windows, so it still runs if they are missing.

## Tools and runtimes

| Tool | Needed by | Install |
|---|---|---|
| Windows 10/11, PowerShell | all | built in |
| Git | install | `winget install Git.Git` |
| Node.js (npx) | hyperframes, skills CLI | `winget install OpenJS.NodeJS.LTS` |
| FFmpeg + ffprobe (full build, with NVENC / libass) | all | `winget install Gyan.FFmpeg` |
| [uv](https://docs.astral.sh/uv/) | video-packaging, video-edit | `winget install astral-sh.uv` |
| Python 3.10+ | all scripts | `winget install Python.Python.3.12` |
| NVIDIA GPU + driver (optional; CPU fallback) | video-edit | vendor driver |
| Google Chrome | video-edit research, gameplay-longform-shorts cards (headless) | `winget install Google.Chrome` |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) in `~/.local/bin` | yt-reference, agent-reach | `uv tool install yt-dlp` |
| OBS Studio + Aitum Vertical plugin | ps5-obs-setup | `winget install OBSProject.OBSStudio` |
| DeepFilterNet in `~/.deepfilter-venv` (Python 3.11, CPU torch 2.1.2) | voice-enhance | see `skills/voice-enhance/SKILL.md` |
| Agent Reach in `~/.agent-reach-venv` (optional) | agent-reach | see `skills/agent-reach/SKILL.md` |

## Python packages

| Package | Needed by | Install |
|---|---|---|
| `edge-tts` | faceless-vo-script | `pip install -r skills/faceless-vo-script/requirements.txt` |
| `pillow`, `numpy` | video-packaging | `uv run` handles it, or `pip install -r skills/video-packaging/requirements.txt` |
| `faster-whisper`, `video-timeline-copilot` (`vtc`) | video-edit | `uv tool install video-timeline-copilot --with faster-whisper` |

## Voice cloning (own-voice-render only)

| Item | Notes |
|---|---|
| NVIDIA GPU (about 6 GB for fine-tuning) | required; CPU is too slow |
| Conda env, Python 3.10, CUDA torch, `transformers==4.49.0` | see `skills/own-voice-render/README.md` |
| Hugging Face account + access to gated `ai4bharat/IndicF5` | log in yourself with `hf auth login`; never share the token |
| Your own recordings | not in this repo; see `skills/own-voice-render/voice/refs/README.md` |

## MCP connectors (optional)

| Connector | Needed by | Notes |
|---|---|---|
| SnipSound `https://mcp.snipsound.com/mcp` | video-edit (music/SFX) | free, no account. `claude mcp add --transport http snipsound https://mcp.snipsound.com/mcp` |
| Canva | video-packaging | optional; the local renderer is used when absent |
| Claude in Chrome | video-edit research | optional; headless Chrome is the fallback |