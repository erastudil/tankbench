#!/usr/bin/env python
"""Reset Day Blast runner script.

Minmaxes expiring provider quotas before scheduled renewal cycles.
Enforces hard safety fences:
- Requires explicit confirmation via --blast-authorized
- Fails closed on unmetered pay-as-you-go providers without hard reset ceilings
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from tankbench.reset_blast import run_blast_cli


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="reset_day_blast",
        description="Execute Reset Day Blast workflow to consume expiring subscription quotas under safety fences.",
    )
    parser.add_argument(
        "--blast-authorized",
        action="store_true",
        help="Explicit confirmation flag authorizing quota consumption.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verify safety fences and print target providers without running workloads.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON telemetry.",
    )
    args = parser.parse_args()

    return run_blast_cli(
        blast_authorized=args.blast_authorized,
        dry_run=args.dry_run,
        as_json=args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
