# Start Shorts Studio and open it in the browser.
#   powershell -ExecutionPolicy Bypass -File .\run.ps1
Set-Location -Path $PSScriptRoot
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Write-Host "Run setup.ps1 first."; exit 1 }
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

$port = 8000
foreach ($line in Get-Content ".env") {
    if ($line -match '^\s*PORT\s*=\s*(\d+)') { $port = [int]$Matches[1] }
}
# open the browser a few seconds after the server starts
Start-Job -ScriptBlock { param($p) Start-Sleep -Seconds 4; Start-Process "http://localhost:$p" } -ArgumentList $port | Out-Null
Write-Host "Shorts Studio -> http://localhost:$port   (Ctrl+C to stop)"
& $py app.py
