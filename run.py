#!/usr/bin/env python
"""Tankbench — Zero-setup benchmark runner.

Runs without manual PYTHONPATH configuration.
Zero-friction entrypoint for both non-technical users and automated evaluation.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to sys.path automatically
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from tankbench.cli import main

if __name__ == "__main__":
    sys.exit(main())
