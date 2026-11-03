# Shorts Studio - one-time setup for Windows 11 (PowerShell 5.1 or 7)
# Run from the project folder:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
# Optional background removal for photos:  ... -File .\setup.ps1 -Rembg
param([switch]$Rembg)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Test-Tool([string]$cmd, [string]$arg = "--version") {
    try { & $cmd $arg *> $null; return ($LASTEXITCODE -eq 0) } catch { return $false }
}
function Refresh-Path {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
function Install-IfMissing([string]$name, [string]$cmd, [string]$wingetId) {
    if (Test-Tool $cmd) { Write-Host "[ok] $name found"; return }
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "[..] installing $name via winget"
        winget install -e --id $wingetId --accept-package-agreements --accept-source-agreements
        Refresh-Path
    }
    else {
        Write-Warning "$name not found and winget is not available. Please install '$name' manually and ensure it's on PATH."
    }
    if (-not (Test-Tool $cmd)) {
        Write-Warning "$name was not found. Please install it manually and ensure it's on PATH."
    }
}
Install-IfMissing "Python 3.12" "python" "Python.Python.3.12"
Install-IfMissing "Node.js LTS" "node" "OpenJS.NodeJS.LTS"
Install-IfMissing "FFmpeg" "ffmpeg" "Gyan.FFmpeg"
if (-not (Test-Tool "ffmpeg" "-version")) { Write-Warning "ffmpeg still not on PATH; open a new PowerShell after setup." }

Write-Host "[..] creating folders and .env"
New-Item -ItemType Directory -Force -Path "outputs", "cache" | Out-Null
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env"; Write-Host "[ok] .env created - add your API keys to it" }
else { Write-Host "[ok] .env already exists" }

Write-Host "[..] python virtual environment + packages"
if (-not (Test-Path ".venv\Scripts\python.exe")) { python -m venv .venv }
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt
if ($Rembg) {
    Write-Host "[..] installing rembg (photo background removal)"
    & $py -m pip install rembg onnxruntime
}

Write-Host "[..] installing Remotion (a few minutes)"
Push-Location "remotion"
npm.cmd install
Pop-Location

Write-Host ""
Write-Host "Setup finished."
Write-Host "1) Edit .env and add your keys:  notepad .env"
Write-Host "2) Start the tool:  powershell -ExecutionPolicy Bypass -File .\run.ps1"