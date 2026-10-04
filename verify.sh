#!/usr/bin/env bash
set -euo pipefail

echo "==> Running Tankbench Baseline..."
python run.py baseline

echo "==> Running Tankbench Hardened Grade..."
python run.py grade --overlay fixtures/hardened

echo "==> Running Tankbench Unit Tests..."
python -m unittest discover -s tests -v

echo "==> All Tankbench checks passed!"
