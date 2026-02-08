$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ScriptDir ".venv"

if (-not (Test-Path (Join-Path $VenvDir "Scripts\Activate.ps1"))) {
    Write-Host "Creating virtual environment..."
    python -m venv $VenvDir
}

& (Join-Path $VenvDir "Scripts\Activate.ps1")

$installed = pip show fastapi 2>$null
if (-not $installed) {
    Write-Host "Installing dependencies..."
    pip install -r (Join-Path $ScriptDir "requirements.txt")
}

Write-Host "Starting pyLapse Web UI..."
python (Join-Path $ScriptDir "web_ui.py") @args
