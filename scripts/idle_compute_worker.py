#!/usr/bin/env python
"""Opportunistic Idle Compute Worker runner script.

Dispatches idle compute tasks across:
1. Alice EMap sense decomposition repair and audit batches
2. Snowgate Forum discussion turns across 9 interest categories
3. EasyLM synthetic distillation sample generation and validation
4. Tankbench golden set continuous verification
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tankbench.idle_worker import run_worker_cli


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="idle_compute_worker",
        description="Run opportunistic idle compute tasks across rotating sovereign ecosystem sectors.",
    )
    parser.add_argument("--cycles", type=int, default=4, help="Number of work cycles to run (default: 4)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate idle execution without state mutations")
    parser.add_argument("--json", action="store_true", help="Output raw JSON execution trace")
    args = parser.parse_args()

    return run_worker_cli(
        max_cycles=args.cycles,
        dry_run=args.dry_run,
        as_json=args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
