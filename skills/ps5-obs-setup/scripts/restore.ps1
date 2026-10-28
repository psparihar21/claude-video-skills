# Restore or snapshot the known-good PS5 OBS config.
# Usage:
#   restore.ps1            back up the current config, put the known-good one back, unmute the card's audio input
#   restore.ps1 -Snapshot  save the CURRENT config as the new known-good (after an approved change)
# OBS must be closed: it rewrites its files on exit and would undo the change.
param([switch]$Snapshot)

$skill = Split-Path $PSScriptRoot -Parent
$good  = "$skill\assets\known-good"
$obs   = "$env:APPDATA\obs-studio"
$prof  = "$obs\basic\profiles\PS5_Gameplay"
$scene = "$obs\basic\scenes\PS5.json"
$vert  = "$obs\plugin_config\vertical-canvas\config.json"   # Aitum Vertical settings

if (Get-Process obs64 -ErrorAction SilentlyContinue) { Write-Output "STOP  OBS is running. Close it (not while recording) and run again."; exit 1 }

if ($Snapshot) {
  Copy-Item "$prof\*" "$good\profile\" -Force
  Copy-Item $scene "$good\scenes\PS5.json" -Force
  if (Test-Path $vert) { New-Item -ItemType Directory -Force "$good\vertical" | Out-Null; Copy-Item $vert "$good\vertical\config.json" -Force }
  Write-Output "Saved the current OBS config as known-good in $good"
  exit 0
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$bk = "$obs\backup-$stamp"
New-Item -ItemType Directory -Force $bk | Out-Null
Copy-Item "$obs\user.ini" $bk -ErrorAction SilentlyContinue
if (Test-Path "$obs\basic") { Copy-Item "$obs\basic" "$bk\basic" -Recurse -Force }
Write-Output "Backed up current config to $bk"

New-Item -ItemType Directory -Force $prof, (Split-Path $scene) | Out-Null
Copy-Item "$good\profile\*" "$prof\" -Force
Copy-Item "$good\scenes\PS5.json" $scene -Force
if (Test-Path "$good\vertical\config.json") { New-Item -ItemType Directory -Force (Split-Path $vert) | Out-Null; Copy-Item "$good\vertical\config.json" $vert -Force }
New-Item -ItemType Directory -Force "$env:USERPROFILE\Videos\PS5 Recordings" | Out-Null

# make OBS open this profile and scene collection by default
$u = "$obs\user.ini"
if (Test-Path $u) {
  $t = Get-Content $u -Raw
  $t = $t -replace '(?m)^Profile=.*$','Profile=PS5 Gameplay' -replace '(?m)^ProfileDir=.*$','ProfileDir=PS5_Gameplay' `
          -replace '(?m)^SceneCollection=.*$','SceneCollection=PS5' -replace '(?m)^SceneCollectionFile=.*$','SceneCollectionFile=PS5.json'
  [IO.File]::WriteAllText($u, $t, (New-Object Text.UTF8Encoding $false))
}
Write-Output "Restored profile 'PS5 Gameplay' and scene collection 'PS5'"

# unmute the UGREEN audio input in Windows (it has been found muted, which silences the game track)
$cs = @'
using System; using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAEV2 { int f(); int g(); int h(); int i(); int SetLevel(float l, Guid c); int j(); int GetLevel(out float l); int a(); int b(); int c(); int d(); int SetMute(bool m, Guid c); int GetMute(out bool m); }
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMD2 { int Activate(ref Guid id, int ctx, IntPtr p, [MarshalAs(UnmanagedType.IUnknown)] out object o); }
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDE2 { int a(); int b(); int GetDevice([MarshalAs(UnmanagedType.LPWStr)] string id, out IMMD2 d); }
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDEc2 {}
public static class Ps5ObsFix {
  public static void Unmute(string id) { var e = (IMMDE2)new MMDEc2(); IMMD2 d; Marshal.ThrowExceptionForHR(e.GetDevice(id, out d)); var g = typeof(IAEV2).GUID; object o; Marshal.ThrowExceptionForHR(d.Activate(ref g, 23, IntPtr.Zero, out o)); var v = (IAEV2)o; v.SetMute(false, Guid.Empty); v.SetLevel(1.0f, Guid.Empty); }
}
'@
try {
  if (-not ('Ps5ObsFix' -as [type])) { Add-Type -TypeDefinition $cs }
  [Ps5ObsFix]::Unmute("{0.0.1.00000000}.{f7f1bc56-e206-4266-939f-a49dbe105dfc}")
  Write-Output "UGREEN audio input unmuted at 100%"
} catch { Write-Output "WARN  could not unmute the UGREEN input: $($_.Exception.Message)" }
Write-Output "Done. Start OBS and run check.ps1."
