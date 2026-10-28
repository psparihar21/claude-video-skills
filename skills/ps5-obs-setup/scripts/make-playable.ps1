# OBS marks all 3 audio tracks "default", so some players play track 3 (mic only) and the game seems missing.
# This writes a lossless copy "<name> (play this).mp4" with only track 1 (the full mix) as default.
# Usage: make-playable.ps1 "<recording.mp4>"
param([Parameter(Mandatory=$true)][string]$Path)
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
if (-not (Test-Path -LiteralPath $Path)) { Write-Output "FAIL  file not found: $Path"; exit 1 }
$src = (Resolve-Path -LiteralPath $Path).Path
$dst = Join-Path (Split-Path $src) ("{0} (play this).mp4" -f [IO.Path]::GetFileNameWithoutExtension($src))
& ffmpeg -hide_banner -v error -y -i $src -map 0 -c copy -disposition:a 0 -disposition:a:0 default -movflags +faststart $dst
if ($LASTEXITCODE -ne 0) { Write-Output "FAIL  ffmpeg exit $LASTEXITCODE"; exit 1 }
& ffprobe -v error -show_entries stream=index,codec_type:stream_disposition=default -of compact $dst
Write-Output "Wrote $dst"
