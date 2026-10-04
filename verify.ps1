$ErrorActionPreference = "Stop"

Write-Host "==> Running Tankbench Baseline..."
python run.py baseline
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Running Tankbench Hardened Grade..."
python run.py grade --overlay fixtures/hardened
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> Running Tankbench Unit Tests..."
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> All Tankbench checks passed!"
