# Windows built-in OCR (Windows.Media.Ocr). Input: image paths as args. Output: one JSON line per image.
# Free, offline, no install. Used by package.py to flag burned-in text; never required.
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Paths)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $task = $asTask.MakeGenericMethod($t).Invoke($null, @($op)); $task.Wait(-1) | Out-Null; $task.Result }
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if ($null -eq $engine) { Write-Output '{"error":"no OCR language installed"}'; exit 0 }
foreach ($p in $Paths) {
  try {
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path $p).Path)) ([Windows.Storage.StorageFile])
    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $res = Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
    $lines = @()
    foreach ($l in $res.Lines) {
      $ws = $l.Words | ForEach-Object { $_.BoundingRect }
      $x0 = ($ws | Measure-Object X -Minimum).Minimum; $y0 = ($ws | Measure-Object Y -Minimum).Minimum
      $x1 = ($ws | ForEach-Object { $_.X + $_.Width } | Measure-Object -Maximum).Maximum
      $y1 = ($ws | ForEach-Object { $_.Y + $_.Height } | Measure-Object -Maximum).Maximum
      $lines += [ordered]@{ text = $l.Text; box = @([int]$x0, [int]$y0, [int]$x1, [int]$y1) }
    }
    $stream.Dispose()
    [ordered]@{ path = $p; w = $dec.PixelWidth; h = $dec.PixelHeight; lines = $lines } | ConvertTo-Json -Compress -Depth 5
  } catch { [ordered]@{ path = $p; error = $_.Exception.Message } | ConvertTo-Json -Compress }
}
