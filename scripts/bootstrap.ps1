$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
Write-Host "Bootstrap complete"
