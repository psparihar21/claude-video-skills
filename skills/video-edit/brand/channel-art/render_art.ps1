<#
Renders the Pushpstation channel art from art.html with headless Chrome.
  .\render_art.ps1 -OutDir "%USERPROFILE%\Videos\pipeline\channel-art" [-Highlights "GAMEPLAY,NEWS,TECH,SHORTS,SETUP"]
Writes YouTube profile (800), Instagram profile (1080), YouTube banner (JPG under 6 MB), a transparent
150x150 watermark, highlight covers, plus banner-safe-area-check.png (red box = text-safe area).
#>
param([Parameter(Mandatory)][string]$OutDir, [string]$Highlights = "GAMEPLAY,NEWS,TECH,SHORTS,SETUP")
$ErrorActionPreference = "Continue"
$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$art = "file:///" + ((Join-Path $PSScriptRoot "art.html") -replace "\\", "/")
New-Item -ItemType Directory -Force $OutDir | Out-Null
function Shot($hash, $w, $h, $png) {
  $out = Join-Path $OutDir $png
  Remove-Item $out -ErrorAction SilentlyContinue
  & $chrome --headless=new --disable-gpu --hide-scrollbars --default-background-color=00000000 --force-device-scale-factor=1 `
    --virtual-time-budget=4000 --window-size=$w,$h --screenshot="$out" "$art#$hash" 2>$null | Out-Null
  for ($i = 0; $i -lt 50 -and -not (Test-Path $out); $i++) { Start-Sleep -Milliseconds 200 }  # Chrome returns before the file lands
  if (-not (Test-Path $out)) { throw "no screenshot for $hash" }
}
Shot "profile-800" 800 800 "youtube-profile-800.png"
Shot "profile-1080" 1080 1080 "instagram-profile-1080.png"
Shot "banner" 2560 1440 "banner.png"
Shot "watermark" 150 150 "youtube-watermark-150.png"
$i = 0
foreach ($h in $Highlights.Split(",")) {
  $c = if ($i % 2) { "y" } else { "v" }
  Shot "hl-$c-$([uri]::EscapeDataString($h.Trim()))" 1080 1920 ("instagram-highlight-{0:00}-{1}.png" -f ($i + 1), $h.Trim().ToLower())
  $i++
}
# JPG copies where the platforms prefer them; banner must stay under 6 MB
Push-Location $OutDir
ffmpeg -v error -y -i banner.png -q:v 2 youtube-banner-2560x1440.jpg
ffmpeg -v error -y -i youtube-profile-800.png -q:v 2 youtube-profile-800.jpg
ffmpeg -v error -y -i instagram-profile-1080.png -q:v 2 instagram-profile-1080.jpg
ffmpeg -v error -y -i banner.png -vf "drawbox=x=507:y=508:w=1546:h=423:color=red@0.9:t=6" banner-safe-area-check.png
Remove-Item banner.png, youtube-profile-800.png, instagram-profile-1080.png
Pop-Location
Get-ChildItem $OutDir | Select-Object Name, @{n = "KB"; e = { [int]($_.Length / 1KB) } }
