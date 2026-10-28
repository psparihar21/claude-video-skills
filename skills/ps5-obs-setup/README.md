# ps5-obs-setup

Checks, repairs or changes a PS5 gameplay recording setup in OBS on Windows (UGREEN 25773 capture card, USB mic, phone facecam over VDO.Ninja, 3 audio tracks, Aitum Vertical 9:16).

## Requirements

OBS Studio, Aitum Vertical plugin, ffmpeg, Windows PowerShell 5.1.

## Scripts / usage

`check.ps1 [-Signal]` (read-only health check), `restore.ps1` (put the known-good config back) / `restore.ps1 -Snapshot` (save yours), `open-obs.ps1`, `make-playable.ps1 <recording>`.

The full workflow Claude follows is in [`SKILL.md`](SKILL.md).

## Privacy and safety

Machine-specific. The known-good snapshot (`assets/known-good/`) is **not** in this repo: it holds your device ids and your private VDO.Ninja stream id (anyone with that id can watch your camera). Run `restore.ps1 -Snapshot` once your setup works to create your own. Audio device ids in `check.ps1`/`restore.ps1` are the author's; replace them with yours (OBS log or `Get-PnpDevice`).
