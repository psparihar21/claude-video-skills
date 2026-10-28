# Render a cut list to an HEVC file one segment at a time, then concat. Never put all segments in one filter graph
# at 4K: ffmpeg runs out of memory ("Cannot allocate memory") and writes an empty file.
# usage: render_segments.ps1 -Source v.mp4 -Segments keep.txt -Audio final.m4a -Out out.mp4 [-Width 3840 -Height 2160]
#        [-SourceOffset 0.92] [-Punch] [-TitlePng t.png -TitleSeconds 2.85] [-OutroPng o.png -OutroSeconds 9] [-Cq 21] [-WorkDir dir]
# -SourceOffset: add to every start when the picture file runs ahead of the audio timeline (vertical = horizontal + 0.92).
# -OutroSeconds: the last N seconds of the last segment get the outro card (add a real-footage tail segment first for Shorts).
param([Parameter(Mandatory)][string]$Source,[Parameter(Mandatory)][string]$Segments,[Parameter(Mandatory)][string]$Audio,
      [Parameter(Mandatory)][string]$Out,[int]$Width=3840,[int]$Height=2160,[double]$SourceOffset=0,[switch]$Punch,
      [string]$TitlePng,[double]$TitleSeconds=2.85,[string]$OutroPng,[double]$OutroSeconds=0,[int]$Cq=21,
      [string]$WorkDir=(Join-Path $env:TEMP "gls-render"))
$ErrorActionPreference='Stop'; New-Item -ItemType Directory -Force $WorkDir | Out-Null
$rows=New-Object System.Collections.ArrayList
foreach($l in Get-Content $Segments){ if($l.Trim()){ $p=$l.Trim().Split(' '); [void]$rows.Add(@([double]$p[0],[double]$p[1])) } }
if($OutroSeconds -gt 0){ $L=$rows[$rows.Count-1]; $rows[$rows.Count-1]=@($L[0],($L[1]-$OutroSeconds)); [void]$rows.Add(@(($L[1]-$OutroSeconds),$L[1])) }
$enc='-c:v','hevc_nvenc','-preset','p7','-tune','hq','-rc','vbr','-cq',"$Cq",'-b:v','0','-tag:v','hvc1','-r','60','-g','60','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv'
$n=$rows.Count; $zoomExpr='(1+0.1*max(0,1-t/0.2))'; $list=@()
for($i=0;$i -lt $n;$i++){
  $start=$rows[$i][0]+$SourceOffset; $len=$rows[$i][1]-$rows[$i][0]; $seg=Join-Path $WorkDir ("s{0:000}.mp4" -f $i)
  $scale= if($Punch -and $i -gt 0 -and $i -lt $n-1){
    "scale=w='trunc($Width*$zoomExpr/2)*2':h='trunc($Height*$zoomExpr/2)*2':eval=frame:flags=lanczos,crop=${Width}:${Height}:x='(trunc($Width*$zoomExpr/2)*2-$Width)/2':y='(trunc($Height*$zoomExpr/2)*2-$Height)/2'"
  } else { "scale=${Width}:${Height}:flags=lanczos" }
  $ov=$null; $ovFilter=""
  if($i -eq 0 -and $TitlePng){ $ov=$TitlePng; $ovFilter="[1:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st=$($TitleSeconds-0.3):d=0.3:alpha=1[o];[b][o]overlay=enable='lte(t,$TitleSeconds)'," }
  if($i -eq $n-1 -and $OutroPng -and $OutroSeconds -gt 0){ $ov=$OutroPng; $ovFilter="[1:v]format=rgba,fade=t=in:st=0:d=0.4:alpha=1[o];[b][o]overlay," }
  if($ov){
    $fc="[0:v]setpts=PTS-STARTPTS,$scale,cas=0.35[b];${ovFilter}format=yuv420p[vo]"
    ffmpeg -y -v error -hwaccel cuda -ss $start -t $len -i $Source -loop 1 -framerate 60 -t $len -i $ov -filter_complex $fc -map '[vo]' -an @enc $seg
  } else {
    ffmpeg -y -v error -hwaccel cuda -ss $start -t $len -i $Source -vf "setpts=PTS-STARTPTS,$scale,cas=0.35,format=yuv420p" -an @enc $seg
  }
  if($LASTEXITCODE){ throw "segment $i failed" }
  $list += "file '$(($seg -replace '\\','/') -replace "'","'\''")'"  # concat demuxer quoting
}
Set-Content "$WorkDir\list.txt" $list -Encoding ascii
ffmpeg -y -v error -f concat -safe 0 -i "$WorkDir\list.txt" -c copy "$WorkDir\video.mp4"
ffmpeg -y -v error -i "$WorkDir\video.mp4" -i $Audio -map 0:v -map 1:a -c copy -movflags +faststart $Out
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,duration -of compact $Out
