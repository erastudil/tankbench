#!/usr/bin/env python
"""Opportunistic Idle Compute Worker runner script.

Weighted Priority Scheduling:
1. Alice EMap sense decomposition repair (40% Weight)
2. EasyLM synthetic distillation (40% Weight)
3. Snowgate Forum RSS chatter (10% Weight)
4. Tankbench golden verification & Progen invariant fuzzing (10% Weight)
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
        description="Run opportunistic idle compute tasks across weighted sovereign ecosystem sectors.",
    )
    parser.add_argument("--cycles", type=int, default=10, help="Number of work cycles to run (default: 10)")
    parser.add_argument("--continuous", action="store_true", help="Run persistently in background until priority interrupt")
    parser.add_argument("--interval", type=float, default=0.005, help="Sleep interval in seconds between cycles (default: 0.005)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate idle execution without state mutations")
    parser.add_argument("--json", action="store_true", help="Output raw JSON execution trace")
    args = parser.parse_args()

    return run_worker_cli(
        max_cycles=args.cycles,
        dry_run=args.dry_run,
        as_json=args.json,
        sample_interval_s=args.interval,
        continuous=args.continuous,
    )


if __name__ == "__main__":
    sys.exit(main())
