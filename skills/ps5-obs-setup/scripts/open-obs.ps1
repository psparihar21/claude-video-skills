# Open OBS the way the user wants it: ready to record 16:9 + 9:16 together (does NOT start recording).
# Safe to run when OBS is already open (it leaves a recording session alone).
$exe = "C:\Program Files\obs-studio\bin\64bit\obs64.exe"
$p = Get-Process obs64 -ErrorAction SilentlyContinue
if ($p) { Write-Output "OBS is already running (pid $($p.Id)). Nothing to do."; exit 0 }
if (-not (Test-Path "C:\ProgramData\obs-studio\plugins\vertical-canvas\bin\64bit\vertical-canvas.dll")) { Write-Output "FAIL  Aitum Vertical plugin missing (see SKILL.md, Vertical canvas)"; exit 1 }
# the card needs a few seconds to be released after OBS closes, else DShow says 0x800705AA and every recording is black
Start-Sleep 8
Start-Process $exe -WorkingDirectory (Split-Path $exe)
Start-Sleep 25
$log = (Get-ChildItem "$env:APPDATA\obs-studio\logs" | Sort-Object Name | Select-Object -Last 1).FullName
$t = Get-Content $log -Raw
if ($t -match "Run failed") { Write-Output "FAIL  capture card did not start (0x800705AA). Close OBS, wait 10 s, run again."; exit 1 }
if ($t -notmatch "Vertical Canvas\] Loaded configuration") { Write-Output "WARN  vertical canvas config not loaded" }
Write-Output "OBS is open. Ctrl+Alt+R starts 16:9 + 9:16, Ctrl+Alt+S stops both."
# the VDO.Ninja stream id is private (anyone who has it can watch the camera): read it from the scene, never hardcode it
$vdo = [regex]::Match((Get-Content "$env:APPDATA\obs-studio\basic\scenes\PS5.json" -Raw -ErrorAction SilentlyContinue), 'vdo\.ninja/\?view=([^&"]+)').Groups[1].Value
Write-Output "Before recording: phone sending to vdo.ninja ?view=$vdo, fifine mic plugged in."
