# Security policy

## Reporting

Found a leaked secret, personal data, or a script that could do harm? Open a
[private security advisory](https://github.com/psparihar21/claude-video-skills/security/advisories/new)
rather than a public issue. If you find a real key, also tell the owner of the service so they can revoke it.

## What this repo must never contain

- API keys, tokens, passwords, private keys, `.env` files
- Personal config (`own-voice-render/config.json`), voice recordings (`own-voice-render/voice/refs/*.wav`),
  the OBS known-good snapshot (`ps5-obs-setup/assets/known-good/`), the channel style card
- Home-folder paths with a real user name (write `%USERPROFILE%` or `~`), personal e-mail addresses
- Private stream links (a VDO.Ninja `?view=` / `?push=` id lets anyone watch the camera)

`.gitignore` keeps the personal files out, `tools/privacy_scan.py` checks the content, and
`.github/workflows/security.yml` runs it with gitleaks on every push and pull request.

## Before you commit

```powershell
git config core.hooksPath .githooks          # once per clone: scan staged files on every commit
python tools/privacy_scan.py                 # full scan of the working tree
python tools/privacy_scan.py --self-test     # check the scanner itself
```

Commit with your GitHub no-reply address so your e-mail stays private:

```powershell
git config user.email "<id>+<username>@users.noreply.github.com"
```

## How the skills handle risk

- No skill stores or asks for a token. Logins (for example `hf auth login`) are done by you in your own terminal.
- Download skills use public links only, never your cookies or accounts, and pass links to `yt-dlp` after `--`.
- Downloaded files go into a new empty folder; their text is data, never instructions.
- Nothing is posted or uploaded for you; replies, titles and descriptions are drafts.
- Scripts call ffmpeg and other tools with argument lists (no shell string building) and clean up temp copies
  of voice audio.
