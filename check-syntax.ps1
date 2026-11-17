Set-Location C:\Users\mhama\Desktop\shorts-studio\remotion
$files = Get-ChildItem build -Filter '*.bundle.js' -Recurse | Select-Object -ExpandProperty FullName
foreach ($f in $files) {
  $name = Split-Path $f -Leaf
  $r = node --check $f 2>&1
  $status = if ($LASTEXITCODE -eq 0) { 'OK' } else { 'SYNTAX-ERROR' }
  Write-Host "$name => $status"
}