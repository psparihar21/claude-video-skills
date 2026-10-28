# Voice + game mix for a cut list, then two-pass loudness. Voice -16 LUFS, game -23 ducked under the voice,
# final -14 LUFS, true peak <= -2.5 dB before AAC (peaks stayed under -1.5 dB after encode).
# usage: mix_audio.ps1 -Game game.wav -Mic mic.wav -Segments keep.txt -Out final.m4a [-FadeOut 3.2] [-WorkDir dir]
# Segments are 'start end' seconds in the stems' own timeline (horizontal time, even when the picture is the vertical file).
param([Parameter(Mandatory)][string]$Game,[Parameter(Mandatory)][string]$Mic,[Parameter(Mandatory)][string]$Segments,
      [Parameter(Mandatory)][string]$Out,[double]$FadeOut=0,[string]$WorkDir=(Join-Path $env:TEMP "gls-mix"))
$ErrorActionPreference='Continue'; New-Item -ItemType Directory -Force $WorkDir | Out-Null
ffmpeg -y -v error -i $Mic -af "highpass=f=80,acompressor=threshold=-24dB:ratio=3:attack=10:release=150,loudnorm=I=-16:TP=-3:LRA=7" -ac 1 -ar 48000 "$WorkDir\voice.wav"
ffmpeg -y -v error -i $Game -af "loudnorm=I=-23:TP=-3:LRA=12" -ar 48000 "$WorkDir\game_n.wav"
ffmpeg -y -v error -i "$WorkDir\game_n.wav" -i "$WorkDir\voice.wav" -filter_complex "[1]asplit[v1][v2];[0][v1]sidechaincompress=threshold=0.02:ratio=5:attack=20:release=400[gd];[gd][v2]amix=inputs=2:normalize=0,alimiter=limit=0.89" -ac 2 -ar 48000 "$WorkDir\mix.wav"
$rows=@(Get-Content $Segments | ? { $_.Trim() } | % { $p=$_.Trim().Split(' '); ,@([double]$p[0],[double]$p[1]) })
$f=New-Object System.Text.StringBuilder; $tot=0.0
for($i=0;$i -lt $rows.Count;$i++){ $a=$rows[$i][0]; $b=$rows[$i][1]; $dur=$b-$a; $tot+=$dur
  [void]$f.AppendLine("[0:a]atrim=${a}:${b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=$([math]::Round($dur-0.02,3)):d=0.02[a$i];") }
$ins=(0..($rows.Count-1) | % { "[a$_]" }) -join ""
$tail= if($FadeOut -gt 0){ ",afade=t=out:st=$([math]::Round($tot-$FadeOut,2)):d=$FadeOut" } else { "" }
[void]$f.AppendLine("${ins}concat=n=$($rows.Count):v=0:a=1${tail}[ac]")
Set-Content "$WorkDir\a.filter" $f.ToString() -Encoding ascii
ffmpeg -y -v error -i "$WorkDir\mix.wav" -/filter_complex "$WorkDir\a.filter" -map '[ac]' -ar 48000 "$WorkDir\cut.wav"
$j=(ffmpeg -hide_banner -nostats -i "$WorkDir\cut.wav" -af 'loudnorm=I=-14:TP=-2.5:LRA=11:print_format=json' -f null - 2>&1 | Out-String)
$m=[regex]::Match($j,'\{[^{}]*"input_i"[^{}]*\}').Value | ConvertFrom-Json
$ln="loudnorm=I=-14:TP=-2.5:LRA=11:measured_I=$($m.input_i):measured_TP=$($m.input_tp):measured_LRA=$($m.input_lra):measured_thresh=$($m.input_thresh):offset=$($m.target_offset):linear=true,alimiter=limit=0.7:level=disabled"
ffmpeg -y -v error -i "$WorkDir\cut.wav" -af $ln -c:a aac -b:a 256k -ar 48000 $Out
$r=ffmpeg -hide_banner -nostats -i $Out -af ebur128=peak=true -f null - 2>&1 | Select-String '^\s+(I:|Peak:)' | % { $_.Line.Trim() }
"total $([math]::Round($tot,1)) s; $($r -join ' ')"

