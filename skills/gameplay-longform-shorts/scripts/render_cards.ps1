# Render the three cards to 2x PNGs (4K long, 2160x3840 Shorts) with headless Chrome. Fills {{TOKENS}}.
# usage: render_cards.ps1 -OutDir dir -Game MYCOPUNK -Subline "PS5 GAMEPLAY  ·  PS PLUS" -NextGame "MAFIA: THE OLD COUNTRY" [-Poster poster.png]
# The poster must be a real key-art crop with no UI, avatar or gamertag (see references/choices.md).
param([Parameter(Mandatory)][string]$OutDir,[Parameter(Mandatory)][string]$Game,[string]$Subline="PS5 GAMEPLAY",
      [Parameter(Mandatory)][string]$NextGame,[string]$Poster)
$ErrorActionPreference='Stop'; New-Item -ItemType Directory -Force $OutDir | Out-Null
$chrome="C:\Program Files\Google\Chrome\Application\chrome.exe"; $cards=Join-Path $PSScriptRoot "..\cards"
if($Poster){ Copy-Item $Poster (Join-Path $OutDir "poster.png") -Force }
$jobs=@(@("outro_long",1920,1080),@("outro_short",1080,1920))
if($Poster){ $jobs+=,@("title_short",1080,1920) }
foreach($j in $jobs){
  $html=(Get-Content (Join-Path $cards "$($j[0]).html") -Raw -Encoding utf8).Replace('{{NEXT_GAME}}',[Net.WebUtility]::HtmlEncode($NextGame)).Replace('{{GAME}}',[Net.WebUtility]::HtmlEncode($Game)).Replace('{{SUBLINE}}',[Net.WebUtility]::HtmlEncode($Subline))
  $h=Join-Path $OutDir "$($j[0]).html"; [IO.File]::WriteAllText($h,$html,(New-Object Text.UTF8Encoding($false)))
  $png="$OutDir\$($j[0])_4k.png"; Remove-Item -LiteralPath $png -Force -ErrorAction SilentlyContinue
  & $chrome --headless=new --default-background-color=00000000 --force-device-scale-factor=2 --window-size="$($j[1]),$($j[2])" --screenshot="$OutDir\$($j[0])_4k.png" ("file:///"+($h -replace '\\','/')) 2>$null
  for($w=0;$w -lt 40 -and -not (Test-Path $png);$w++){ Start-Sleep -Milliseconds 500 }  # Chrome returns before the PNG is written
}
Get-ChildItem $OutDir -Filter *_4k.png | select Name,Length

