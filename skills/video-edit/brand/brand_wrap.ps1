<#
Adds the Pushpstation gaming pack (v2) to a finished edit.
  long : 2.9 s slash sting at -IntroAt (where the cold-open hook ends), slash transitions centred on each
         -Cuts time, a subscribe-click at -SubAt (default 6 s before the end), and a 15 s end screen
         whose slash wipe starts 0.42 s before the last frame (YouTube end-screen slots marked).
  short: 2.6 s "NOW PLAYING" band over the hook at 0 s, and a 3.6 s full-frame end card with the
         subscribe click on the last 3.6 s (skip it with -NoOutro). Nothing is appended.
Graphics render per video through HyperFrames (alpha ProRes 4444) at the video's own resolution.

  .\brand_wrap.ps1 -Video final.mp4 -Mode long -IntroAt 6.5 -Note "Mafia: The Old Country" -Cuts "95.2,301.8" -Out final-branded.mp4
  .\brand_wrap.ps1 -Video short.mp4 -Mode short -Note "Mafia: The Old Country" -Out short-branded.mp4
#>
param(
  [Parameter(Mandatory)][string]$Video,
  [Parameter(Mandatory)][ValidateSet("long","short")][string]$Mode,
  [Parameter(Mandatory)][string]$Out,
  [string]$Note = "PS5 Gameplay",         # game name
  [string]$Tag = "NOW PLAYING",
  [double]$IntroAt = -1,                  # long: second where the hook ends; required for long
  [string]$Cuts = "",                     # long: comma-separated cut times that get a slash transition
  [double]$SubAt = -1,                    # long: subscribe click start; default 6 s before the end
  [string]$Next = "MORE GAMEPLAY SOON",   # long end screen, top right
  [string]$Right = "BEST VIDEO",          # long end screen, right slot label
  [string]$Music = "",                    # long end screen bed (SnipSound file); default = muffled tail audio
  [switch]$NoOutro                        # short only: the format already ends on its own outro scene
)
$ErrorActionPreference = "Continue"  # PS 5.1 turns native stderr into errors under Stop; exit codes are checked instead
if ($Mode -eq "long" -and $IntroAt -lt 0) { throw "-IntroAt is required for long videos: the second the cold-open hook ends." }
$env:Path += ";$env:APPDATA\npm"; $env:HYPERFRAMES_SKIP_SKILLS = "1"
$hf = Join-Path $PSScriptRoot "hf"; $sfx = Join-Path $PSScriptRoot "sfx"
$tmp = Join-Path $env:TEMP ("pushp-brand-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Force $tmp | Out-Null
$Video = (Resolve-Path $Video).Path
$inv = [Globalization.CultureInfo]::InvariantCulture
function n($x) { ([double]$x).ToString("0.###", $inv) }

# --- probe
$p = (& ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 $Video).Split(",")
$codec = $p[0]; $W = [int]$p[1]; $H = [int]$p[2]
$fps = [math]::Round(([double]$p[3].Split("/")[0]) / ([double]$p[3].Split("/")[1]))
$dur = [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $Video)
$hasA = [bool](& ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 $Video)
$portrait = $H -gt $W
if (($Mode -eq "short") -ne $portrait) { throw "Mode $Mode does not match a ${W}x${H} video." }
$res = if ($portrait) { if ($H -ge 3840) { "portrait-4k" } else { "portrait" } } else { if ($W -ge 3840) { "landscape-4k" } else { "landscape" } }
Write-Host "video ${W}x${H} ${fps}fps $codec, $(n $dur) s, audio=$hasA -> $res"

# --- render graphics
function Render($comp, $vars, $f) {
  $vf = Join-Path $tmp "$comp.json"
  [IO.File]::WriteAllText($vf, ($vars | ConvertTo-Json -Compress), (New-Object Text.UTF8Encoding $false))
  Push-Location $hf
  & hyperframes render -c "$comp.html" --format mov --fps $f --resolution $res -o (Join-Path $tmp "$comp.mov") --variables-file $vf --quiet *> (Join-Path $tmp "$comp.log")
  Pop-Location
  if (-not (Test-Path (Join-Path $tmp "$comp.mov"))) { throw "HyperFrames render of $comp failed, see $tmp\$comp.log" }
}
$gf = [math]::Min($fps, 60)
$cutList = @($Cuts.Split(",") | Where-Object { $_.Trim() } | ForEach-Object { [double]::Parse($_.Trim(), $inv) })
if ($Mode -eq "long") {
  Render "intro_long" @{ note = $Note; tag = $Tag } $gf
  Render "subscribe" @{} $gf
  Render "outro_long" @{ next = $Next; right = $Right } 30   # 30 fps keeps the 15 s render quick; motion is slow
  if ($cutList.Count) { Render "transition" @{} $gf }
} else {
  Render "intro_short" @{ note = $Note; tag = $Tag } $gf
  if (-not $NoOutro) { Render "outro_short" @{} $gf }
}

# --- composite
$enc = if ($codec -eq "hevc") { "hevc_nvenc" } else { "h264_nvenc" }
$ia = if ($hasA) { "[0:a]aresample=48000,aformat=channel_layouts=stereo" } else { "anullsrc=r=48000:cl=stereo,atrim=0:$(n $dur)" }
$ins = @("-i", $Video); $g = @(); $mixes = @()
function AddIn($path) { $script:ins += @("-i", $path); return (@($script:ins | Where-Object { $_ -eq "-i" }).Count - 1) }
# overlay graphic $v (input index) at time $t; sound $s at the same time
function Place($label, $v, $s, $t, $len) {
  $script:g += "[$($v):v]setpts=PTS-STARTPTS+$(n $t)/TB[o$label]"
  $script:g += "[cur][o$label]overlay=enable='between(t,$(n $t),$(n ($t + $len)))':eof_action=pass:format=auto[cur]"
  $script:g += "[$($s):a]adelay=$([int]($t * 1000)):all=1[a$label]"; $script:mixes += "[a$label]"
}
if ($Mode -eq "long") {
  $oStart = $dur - 0.42; $total = $oStart + 15
  if ($SubAt -lt 0) { $SubAt = [math]::Max(0, $dur - 6) }
  $g += "[0:v]tpad=stop_mode=clone:stop_duration=$(n ($total - $dur)),format=yuv420p[cur]"
  Place "i" (AddIn "$tmp\intro_long.mov") (AddIn "$sfx\intro_long.wav") $IntroAt 2.9
  if ($cutList.Count) {
    $tv = AddIn "$tmp\transition.mov"; $ts = AddIn "$sfx\transition.wav"
    $g += "[$($tv):v]split=$($cutList.Count)" + (($cutList | ForEach-Object -Begin { $k = 0 } -Process { "[tv$k]"; $k++ }) -join "")
    $g += "[$($ts):a]asplit=$($cutList.Count)" + (($cutList | ForEach-Object -Begin { $k = 0 } -Process { "[ts$k]"; $k++ }) -join "")
    for ($k = 0; $k -lt $cutList.Count; $k++) {
      $t = $cutList[$k] - 0.46
      $g += "[tv$k]setpts=PTS-STARTPTS+$(n $t)/TB[ot$k]"
      $g += "[cur][ot$k]overlay=enable='between(t,$(n $t),$(n ($t + 1)))':eof_action=pass:format=auto[cur]"
      $g += "[ts$k]adelay=$([int]($t * 1000)):all=1[at$k]"; $mixes += "[at$k]"
    }
  }
  Place "s" (AddIn "$tmp\subscribe.mov") (AddIn "$sfx\subscribe.wav") $SubAt 3.4
  Place "o" (AddIn "$tmp\outro_long.mov") (AddIn "$sfx\outro_long.wav") $oStart 15
  $g += "[cur]fade=t=out:st=$(n ($total - 0.6)):d=0.6,format=yuv420p[v]"
  # bed under the end screen: SnipSound music if given, else the last 15 s muffled
  if ($Music) { $mi = AddIn $Music; $g += "[$($mi):a]atrim=0:15,asetpts=PTS-STARTPTS,loudnorm=I=-24:TP=-4,afade=t=in:d=0.6,afade=t=out:st=13.4:d=1.6,adelay=$([int]($dur * 1000)):all=1[bed]" }
  elseif ($hasA) { $ins += @("-ss", (n ([math]::Max(0, $dur - 15)))); $ti = AddIn $Video
    $g += "[$($ti):a]atrim=0:15,asetpts=PTS-STARTPTS,lowpass=f=700,volume=-14dB,afade=t=in:d=0.4,afade=t=out:st=12.5:d=2.5,adelay=$([int]($dur * 1000)):all=1[bed]" }
  else { $g += "anullsrc=r=48000:cl=stereo,atrim=0:1[bed]" }
  $g += "$ia,apad=whole_dur=$(n $total)[a0]"
  $g += "[a0][bed]" + ($mixes -join "") + "amix=$($mixes.Count + 2):normalize=0:duration=first,atrim=0:$(n $total),afade=t=out:st=$(n ($total - 0.8)):d=0.8,alimiter=limit=0.79:level=disabled[a]"
} else {
  $g += "[0:v]format=yuv420p[cur]"
  Place "i" (AddIn "$tmp\intro_short.mov") (AddIn "$sfx\intro_short.wav") 0 2.6
  if (-not $NoOutro) { Place "o" (AddIn "$tmp\outro_short.mov") (AddIn "$sfx\outro_short.wav") ([math]::Max(0, $dur - 3.6)) 3.6 }
  $g += "[cur]format=yuv420p[v]"
  $g += "$ia[a0]"
  $g += "[a0]" + ($mixes -join "") + "amix=$($mixes.Count + 1):normalize=0:duration=first,alimiter=limit=0.79:level=disabled[a]"
}
# ffmpeg labels can be reused only once each: number the running [cur] chain
$c = 0; $graph = ($g | ForEach-Object {
  $line = $_
  if ($line -match "^\[cur\]") { $line = $line -replace "^\[cur\]", "[c$c]" }
  if ($line -match "\[cur\]$") { $c++; $line = $line -replace "\[cur\]$", "[c$c]" }
  $line }) -join ";`n"
$gfile = Join-Path $tmp "graph.txt"; [IO.File]::WriteAllText($gfile, $graph)
& ffmpeg -v error -stats -y @ins -/filter_complex $gfile -map "[v]" -map "[a]" -c:v $enc -preset p7 -tune hq -rc vbr -cq 16 -b:v 0 `
  -pix_fmt yuv420p -r $fps -c:a aac -b:a 320k -ar 48000 -movflags +faststart $Out
if ($LASTEXITCODE -ne 0) { throw "ffmpeg failed; graph in $gfile" }

# --- measure
$od = [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $Out)
$lo = (& ffmpeg -hide_banner -nostats -i $Out -af ebur128=peak=true -f null - 2>&1 | Select-String -Pattern "^\s+(I|LRA|Peak):" | ForEach-Object { $_.Line.Trim() }) -join "  "
Write-Host "OUT $Out  $(n $od) s  $lo"
Remove-Item -Recurse -Force $tmp
