from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
import unittest
from pathlib import Path

from tankbench.scoring import Score, fold


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def patient_src() -> Path:
    return repo_root() / "patient"


def copy_patient(dest: Path, overlay: Path | None = None, app: Path | None = None) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(patient_src(), dest, ignore=shutil.ignore_patterns("harbor.db", "__pycache__"))
    if overlay:
        for src in overlay.rglob("*"):
            if src.is_file():
                rel = src.relative_to(overlay)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
    if app:
        shutil.copy2(app, dest / "app.py")
    return dest


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def wait_health(url: str, tries: int = 50) -> None:
    import urllib.error
    import urllib.request

    for _ in range(tries):
        try:
            with urllib.request.urlopen(url + "/health", timeout=0.4) as r:
                if r.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.05)
    raise RuntimeError(f"patient did not come up at {url}")


def _discover(start: Path) -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return loader.discover(str(start), pattern="test_*.py")


def run_tests(url: str, start: Path) -> unittest.TestResult:
    os.environ["TANKBENCH_URL"] = url
    suite = _discover(start)
    buf_runner = unittest.TextTestRunner(verbosity=2, stream=sys.stderr)
    return buf_runner.run(suite)


def names_of(result: unittest.TestResult, attr: str) -> list[str]:
    out = []
    for item in getattr(result, attr):
        test = item[0] if isinstance(item, tuple) else item
        out.append(str(test))
    return out


def score_dir(
    work: Path,
    *,
    expect_baseline: bool = False,
) -> Score:
    port = free_port()
    side = free_port()
    url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["TANKBENCH_HOST"] = "127.0.0.1"
    env["TANKBENCH_PORT"] = str(port)
    env["TANKBENCH_SIDECAR_PORT"] = str(side)
    env["PYTHONUNBUFFERED"] = "1"
    os.environ["TANKBENCH_SIDECAR_PORT"] = str(side)
    proc = subprocess.Popen(
        [sys.executable, str(work / "app.py")],
        cwd=str(work),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_health(url)
        alive = run_tests(url, repo_root() / "spec")
        rounds = run_tests(url, repo_root() / "rounds")
        score = fold(
            alive_ran=alive.testsRun,
            alive_failed=len(alive.failures) + len(alive.errors),
            rounds_ran=rounds.testsRun,
            rounds_hits=rounds.testsRun - (len(rounds.failures) + len(rounds.errors)),
        )
        score.alive_failures = names_of(alive, "failures") + names_of(alive, "errors")
        score.round_misses = names_of(rounds, "failures") + names_of(rounds, "errors")
        if expect_baseline:
            # unpatched patient: every round test must HIT (unittest success)
            if score.alive_failed:
                raise RuntimeError("baseline patient failed alive spec: " + ", ".join(score.alive_failures))
            if score.rounds_hits != score.rounds_ran:
                raise RuntimeError(
                    "baseline rounds must all hit; misses="
                    + ", ".join(score.round_misses)
                )
        return score
    finally:
        proc.kill()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.terminate()


def grade(
    *,
    overlay: Path | None = None,
    app: Path | None = None,
    expect_baseline: bool = False,
) -> Score:
    work = repo_root() / ".work" / ("baseline" if expect_baseline else "grade")
    copy_patient(work, overlay=overlay, app=app)
    return score_dir(work, expect_baseline=expect_baseline)
