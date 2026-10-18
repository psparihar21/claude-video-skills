# Wrapper: always uses the indicf5 env in UTF-8 mode.  Usage: .\ovr.ps1 <command> [args]
$cfg = Get-Content (Join-Path $PSScriptRoot 'config.json') -Raw | ConvertFrom-Json
$env:PYTHONUTF8 = '1'
& $cfg.python -X utf8 (Join-Path $PSScriptRoot 'scripts\ovr.py') @args
exit $LASTEXITCODE
