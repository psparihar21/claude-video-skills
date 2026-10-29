<#
.SYNOPSIS  Installs the skills in this repo, and the third-party skills they depend on, into ~/.claude/skills.
.PARAMETER SkipDependencies  Install only the skills in this repo.
.PARAMETER Target            Skills folder. Default: ~/.claude/skills
#>
param(
  [switch]$SkipDependencies,
  [string]$Target = "$env:USERPROFILE\.claude\skills"
)
$ErrorActionPreference = 'Continue'
$root = $PSScriptRoot
New-Item -ItemType Directory -Force $Target | Out-Null

Write-Host "== Installing skills to $Target"
foreach ($d in Get-ChildItem "$root\skills" -Directory) {
  $dest = Join-Path $Target $d.Name
  if (Test-Path $dest) { Write-Host "   updating $($d.Name)" } else { Write-Host "   adding   $($d.Name)" }
  robocopy $d.FullName $dest /E /XD .venv __pycache__ /NFL /NDL /NJH /NJS | Out-Null
}

if (-not $SkipDependencies) {
  Write-Host "== Checking tools"
  foreach ($t in 'git','node','npx','ffmpeg','ffprobe','uv','python') {
    if (Get-Command $t -ErrorAction SilentlyContinue) { Write-Host "   ok      $t" } else { Write-Host "   MISSING $t  (see dependencies/DEPENDENCIES.md)" -ForegroundColor Yellow }
  }

  Write-Host "== Third-party skills (from their original authors)"
  if (Get-Command npx -ErrorAction SilentlyContinue) {
    npx --yes skills add heygen-com/hyperframes -g -y
    npx --yes skills add nutlope/hallmark -g -y --agent claude-code
  } else { Write-Host "   skipped hyperframes, hallmark: npx not found" -ForegroundColor Yellow }

  foreach ($s in 'clipify','cut-video') {
    $dest = Join-Path $Target $s
    if (Test-Path $dest) { Write-Host "   present $s" }
    elseif (Get-Command git -ErrorAction SilentlyContinue) { git clone --depth 1 "https://github.com/louisedesadeleer/$s.git" $dest }
    else { Write-Host "   skipped ${s}: git not found" -ForegroundColor Yellow }
  }

  Write-Host "== Python packages"
  if (Get-Command python -ErrorAction SilentlyContinue) {
    python -m pip install -q -r "$root\skills\faceless-vo-script\requirements.txt" -r "$root\skills\video-packaging\requirements.txt"
  }
  if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv tool install video-timeline-copilot --with faster-whisper
  }
  Write-Host "== Optional: claude mcp add --transport http snipsound https://mcp.snipsound.com/mcp"
}
Write-Host "Done. Restart Claude Code."