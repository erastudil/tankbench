from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tankbench.harness import grade, repo_root


def _print(score, *, kind: str) -> None:
    payload = {
        "kind": kind,
        "alive": f"{score.alive_ran - score.alive_failed}/{score.alive_ran}",
        "rounds_hit": f"{score.rounds_hits}/{score.rounds_ran}",
        "score": round(score.value, 4),
        "perfect": score.perfect,
        "alive_failures": score.alive_failures,
        "round_misses": score.round_misses,
    }
    print(json.dumps(payload, indent=2))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tankbench")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("baseline", help="unpatched patient: alive pass, every round hits")

    g = sub.add_parser("grade", help="overlay a patch and score")
    g.add_argument("--overlay", type=Path, default=None)
    g.add_argument("--app", type=Path, default=None)

    sub.add_parser("prompt", help="print the harden prompt")

    args = p.parse_args(argv)
    if args.cmd == "prompt":
        sys.stdout.write((repo_root() / "prompts" / "harden.md").read_text(encoding="utf-8"))
        return 0
    if args.cmd == "baseline":
        score = grade(expect_baseline=True)
        _print(score, kind="baseline")
        return 0 if score.alive_ok and score.rounds_hits == score.rounds_ran else 1
    if args.cmd == "grade":
        if not args.overlay and not args.app:
            print("grade needs --overlay DIR or --app FILE", file=sys.stderr)
            return 2
        score = grade(overlay=args.overlay, app=args.app)
        _print(score, kind="grade")
        return 0 if score.perfect else 1
    return 2
