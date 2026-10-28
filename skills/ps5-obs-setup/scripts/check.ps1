# Health check for the PS5 OBS recording setup. Read-only: changes nothing.
# Usage: powershell -ExecutionPolicy Bypass -File check.ps1 [-Signal]
#   -Signal  also grabs 3 s straight from the capture card (picture + sound). Close OBS first.
param([switch]$Signal)

$ErrorActionPreference = 'Continue'
$env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
$fails = 0; $warns = 0
function Ok($m)   { Write-Output "PASS  $m" }
function Bad($m)  { Write-Output "FAIL  $m"; $script:fails++ }
function Warn($m) { Write-Output "WARN  $m"; $script:warns++ }

$obsDir  = "$env:APPDATA\obs-studio"
$profDir = "$obsDir\basic\profiles\PS5_Gameplay"
$scene   = "$obsDir\basic\scenes\PS5.json"
$UgAudioId = "{0.0.1.00000000}.{f7f1bc56-e206-4266-939f-a49dbe105dfc}"
$MicDeviceId      = "{0.0.1.00000000}.{5a259633-ffa3-48fb-95f2-5513f22928cb}"

# --- OBS install and default profile
$exe = "C:\Program Files\obs-studio\bin\64bit\obs64.exe"
if (Test-Path $exe) { Ok "OBS installed $((Get-Item $exe).VersionInfo.ProductVersion)" } else { Bad "OBS not found at $exe" }
$obsRunning = [bool](Get-Process obs64 -ErrorAction SilentlyContinue)
Write-Output "INFO  OBS running: $obsRunning"
$user = Get-Content "$obsDir\user.ini" -Raw -ErrorAction SilentlyContinue
if ($user -match '(?m)^ProfileDir=PS5_Gameplay\s*$' -and $user -match '(?m)^SceneCollectionFile=PS5\.json\s*$') { Ok "default profile 'PS5 Gameplay' + scene collection 'PS5'" }
else { Bad "OBS does not open the PS5 profile/scene collection by default (user.ini [Basic])" }

# --- profile
$ini = Get-Content "$profDir\basic.ini" -Raw -ErrorAction SilentlyContinue
if (-not $ini) { Bad "profile missing: $profDir\basic.ini" } else {
  $want = [ordered]@{ 'BaseCX'='1920'; 'BaseCY'='1080'; 'OutputCX'='1920'; 'OutputCY'='1080'; 'FPSCommon'='60'; 'Mode'='Advanced';
           'RecFormat2'='hybrid_mp4'; 'RecEncoder'='obs_nvenc_hevc_tex'; 'RecTracks'='7'; 'RecFilePath'=("$env:USERPROFILE/Videos/PS5 Recordings" -replace '\\','/') }
  foreach ($k in $want.Keys) {
    $m = [regex]::Match($ini, "(?m)^$k=(.*)$")
    if ($m.Success -and $m.Groups[1].Value.Trim() -eq $want[$k]) { Ok "$k=$($want[$k])" } else { Bad "$k is '$($m.Groups[1].Value.Trim())', expected '$($want[$k])'" }
  }
  if ($ini -match 'StartRecording=.*"alt":true.*OBS_KEY_R' -and $ini -match 'StopRecording=.*"alt":true.*OBS_KEY_S') { Ok "hotkeys Ctrl+Alt+R start / Ctrl+Alt+S stop" }
  else { Warn "record hotkeys are not Ctrl+Alt+R / Ctrl+Alt+S" }
}
if (Test-Path "$env:USERPROFILE\Videos\PS5 Recordings") { $free = [math]::Round((Get-PSDrive C).Free/1GB); Ok "recordings folder exists, C: free ${free} GB (~12 GB per hour)"; if ($free -lt 30) { Warn "less than 30 GB free" } }
else { Bad "recordings folder missing" }

# --- scene collection
try { $j = Get-Content $scene -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $j = $null; Bad "cannot read $scene" }
if ($j) {
  $src = @{}; foreach ($s in $j.sources) { $src[$s.name] = $s }
  $card = $src['PS5 Capture Card (UGREEN)']
  if ($card -and $card.settings.video_device_id -like 'UGREEN 25773:*' -and $card.settings.resolution -eq '1920x1080' -and $card.settings.frame_interval -eq 166666) { Ok "capture card source: UGREEN 1080p60" } else { Bad "capture card source missing or not 1080p60" }
  if ($card -and $card.mixers -eq 0) { Ok "card's own audio off (game sound comes from the WASAPI source)" } else { Warn "card source sends its own audio too (possible double game audio)" }
  $ga = $src['PS5 Game Audio (UGREEN)']
  if ($ga -and $ga.settings.device_id -eq $UgAudioId -and $ga.mixers -eq 3 -and -not $ga.muted) { Ok "game audio source on UGREEN input, tracks 1+2" } else { Bad "game audio source missing, wrong device, muted, or not on tracks 1+2" }
  $mic = $j.AuxAudioDevice1
  if ($mic -and $mic.settings.device_id -eq $MicDeviceId -and $mic.mixers -eq 5 -and -not $mic.muted) { Ok "mic = fifine, tracks 1+3" } else { Bad "mic is not the fifine on tracks 1+3 (or muted)" }
  if ($j.DesktopAudioDevice1) { Warn "desktop audio is enabled (laptop sounds will be recorded)" } else { Ok "desktop audio off" }
  Write-Output ("INFO  mic filters:  " + (($mic.filters | % { $_.name }) -join ' -> '))
  Write-Output ("INFO  game filters: " + (($ga.filters | % { $_.name }) -join ' -> '))
  $sc = $src['PS5 Gameplay']
  foreach ($it in $sc.settings.items) {
    if ($it.name -like 'Facecam*') {
      $r = $it.pos.x + $it.bounds.x
      $inBand = ($it.pos.x -lt 1264) -and ($r -gt 656)
      $msg = "{0}: {1} at {2},{3} size {4}x{5} crop L{6} T{7} R{8} B{9}" -f $it.name, $(if ($it.visible) {'shown'} else {'hidden'}), $it.pos.x, $it.pos.y, $it.bounds.x, $it.bounds.y, $it.crop_left, $it.crop_top, $it.crop_right, $it.crop_bottom
      if ($it.visible -and $inBand) { Bad "$msg - overlaps the 9:16 Shorts band (x 656-1264)" } else { Ok $msg }
    }
  }
  foreach ($n in 'Facecam (phone)','Facecam (laptop)') { if ($src[$n] -and -not $src[$n].settings.deactivate_when_not_showing) { Warn "$n keeps its camera on while hidden" } }
}

# --- devices
$pnp = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue
if ($pnp | ? { $_.Class -eq 'Camera' -and $_.FriendlyName -eq 'UGREEN 25773' }) { Ok "UGREEN capture card connected" } else { Bad "UGREEN capture card not connected (USB)" }
if ($pnp | ? { $_.FriendlyName -like '*fifine*' }) { Ok "fifine mic connected" } else { Bad "fifine mic not connected" }
$ff = (& ffmpeg -hide_banner -list_devices true -f dshow -i dummy 2>&1 | Out-String)
if ($ff -match 'Nothing Phone \(2\) \(Windows Virtual Camera\)') { Ok "phone camera visible to Windows (Phone Link)" } else { Warn "phone camera not visible: phone not linked; laptop camera is the fallback" }

# --- Windows mute state of the card's audio input
$cs = @'
using System; using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAEV { int f(); int g(); int h(); int i(); int SetLevel(float l, Guid c); int j(); int GetLevel(out float l); int a(); int b(); int c(); int d(); int SetMute(bool m, Guid c); int GetMute(out bool m); }
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMD { int Activate(ref Guid id, int ctx, IntPtr p, [MarshalAs(UnmanagedType.IUnknown)] out object o); }
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDE { int a(); int b(); int GetDevice([MarshalAs(UnmanagedType.LPWStr)] string id, out IMMD d); }
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDEc {}
public static class Ps5ObsVol {
  static IAEV Get(string id) { var e = (IMMDE)new MMDEc(); IMMD d; Marshal.ThrowExceptionForHR(e.GetDevice(id, out d)); var g = typeof(IAEV).GUID; object o; Marshal.ThrowExceptionForHR(d.Activate(ref g, 23, IntPtr.Zero, out o)); return (IAEV)o; }
  public static string Read(string id) { var v = Get(id); float l; bool m; v.GetLevel(out l); v.GetMute(out m); return string.Format("{0:0}|{1}", l*100, m); }
}
'@
try { if (-not ('Ps5ObsVol' -as [type])) { Add-Type -TypeDefinition $cs } } catch { Warn "could not load the audio level reader: $($_.Exception.Message)" }
try {
  $ug = ([Ps5ObsVol]::Read($UgAudioId)).Split('|')
  if ($ug[1] -eq 'False' -and [int]$ug[0] -ge 90) { Ok "Windows: UGREEN audio input unmuted at $($ug[0])%" } else { Bad "Windows: UGREEN audio input muted=$($ug[1]) level=$($ug[0])% (game track will be silent)" }
} catch { Warn "Windows: cannot read the UGREEN audio input (card unplugged?)" }
try {
  $mc = ([Ps5ObsVol]::Read($MicDeviceId)).Split('|')
  if ($mc[1] -eq 'False') { Ok "Windows: fifine mic unmuted at $($mc[0])%" } else { Bad "Windows: fifine mic is muted" }
} catch { Warn "Windows: cannot read the fifine mic (unplugged?)" }

# --- last OBS log
$log = Get-ChildItem "$obsDir\logs" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($log) {
  $lines = Get-Content $log.FullName
  $last = ($lines | Select-String 'Recording Start|Recording Stop' | Select-Object -Last 1)
  if ($last) { Write-Output "INFO  last recording event: $($last.Line.Trim())" }
  $skip = $lines | Select-String 'number of skipped frames due to encoding lag: (\d+)/(\d+)' | Select-Object -Last 1
  if ($skip) { $a = [int]$skip.Matches[0].Groups[1].Value; $b = [int]$skip.Matches[0].Groups[2].Value; if ($b -gt 0 -and $a / $b -gt 0.01) { Warn "last recording skipped $a/$b frames (encoder overload)" } else { Ok "last recording skipped $a/$b frames" } }
  if ($lines | Select-String 'WASAPI: Device .Digital Audio Interface \(UGREEN 25773\). .* initialized') { Ok "OBS opened the UGREEN audio input" } elseif ($obsRunning) { Warn "OBS log does not show the UGREEN audio input opening" }
}

# --- optional live signal test
if ($Signal) {
  if ($obsRunning) { Warn "skipping -Signal: close OBS first (the card can only feed one app)" } else {
    $tmp = "$env:LOCALAPPDATA\Temp\ps5-obs-check"; New-Item -ItemType Directory -Force $tmp | Out-Null
    & ffmpeg -hide_banner -v error -y -f dshow -video_size 1920x1080 -framerate 60 -pixel_format yuyv422 -i video="UGREEN 25773" -frames:v 1 "$tmp\card.png" 2>$null
    & ffmpeg -hide_banner -v error -y -f dshow -i audio="Digital Audio Interface (UGREEN 25773)" -t 3 "$tmp\card.wav" 2>$null
    $vol = (& ffmpeg -hide_banner -i "$tmp\card.wav" -af volumedetect -f null - 2>&1 | Select-String 'mean_volume: (-?[\d.]+)')
    if ($vol) { $mv = [double]$vol.Matches[0].Groups[1].Value; if ($mv -gt -70) { Ok "card sound present (mean $mv dB)" } else { Warn "card sound silent (mean $mv dB): PS5 quiet, or PS5 audio output not set to HDMI" } }
    Write-Output "INFO  card frame saved: $tmp\card.png (a UGREEN logo = no signal: turn off HDCP on the PS5)"
  }
}

Write-Output ""
Write-Output "RESULT  $fails fail, $warns warn"
exit [int]($fails -gt 0)
