#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
PYTHON="${PYTHON:-$(command -v python3 2>/dev/null || command -v python 2>/dev/null)}"

echo "==> Running Tankbench Baseline..."
"$PYTHON" run.py baseline

echo "==> Running Tankbench Hardened Grade..."
"$PYTHON" run.py grade --overlay fixtures/hardened

echo "==> Running Tankbench Unit Tests..."
"$PYTHON" -m unittest discover -s tests -v

echo "==> All Tankbench checks passed!"
