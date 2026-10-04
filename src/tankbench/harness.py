from __future__ import annotations

import io
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


def apply_patch(dest: Path, patch_path: Path) -> None:
    patch_file = patch_path.resolve()
    if not patch_file.exists():
        raise FileNotFoundError(f"Patch file not found: {patch_file}")

    raw_bytes = patch_file.read_bytes()
    if raw_bytes.startswith((b"\xff\xfe", b"\xfe\xff")):
        patch_text = raw_bytes.decode("utf-16", errors="replace")
    elif raw_bytes.startswith(b"\xef\xbb\xbf"):
        patch_text = raw_bytes.decode("utf-8-sig", errors="replace")
    else:
        patch_text = raw_bytes.decode("utf-8", errors="replace")

    patch_bytes = patch_text.encode("utf-8")

    applied = False
    errors = []
    for p_level in (1, 0, 2):
        res = subprocess.run(
            [
                "git",
                "-C",
                str(dest),
                "apply",
                f"-p{p_level}",
                "--ignore-space-change",
                "--ignore-whitespace",
                "--unsafe-paths",
                "-",
            ],
            input=patch_bytes,
            capture_output=True,
        )
        if res.returncode == 0:
            applied = True
            break
        errors.append(f"-p{p_level}: {res.stderr.decode('utf-8', errors='replace').strip()}")

    if not applied:
        raise RuntimeError(
            f"Failed to apply patch {patch_file}.\nGit apply errors:\n" + "\n".join(errors)
        )


def copy_patient(
    dest: Path,
    overlay: Path | None = None,
    app: Path | None = None,
    patch: Path | None = None,
) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(patient_src(), dest, ignore=shutil.ignore_patterns("harbor.db", "__pycache__"))
    if overlay:
        prune_file = overlay / ".prune"
        if prune_file.exists():
            for line in prune_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    target = dest / line
                    if target.is_dir():
                        shutil.rmtree(target, ignore_errors=True)
                    elif target.is_file():
                        target.unlink(missing_ok=True)
        for src in overlay.rglob("*"):
            if src.is_file() and src.name != ".prune":
                rel = src.relative_to(overlay)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, target)
    if app:
        shutil.copy2(app, dest / "app.py")
    if patch:
        apply_patch(dest, patch)
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


def run_tests(url: str, start: Path, *, verbose: bool = False) -> unittest.TestResult:
    os.environ["TANKBENCH_URL"] = url
    suite = _discover(start)
    is_v = verbose or os.environ.get("TANKBENCH_VERBOSE") == "1"
    stream = sys.stderr if is_v else io.StringIO()
    runner = unittest.TextTestRunner(verbosity=2 if is_v else 0, stream=stream)
    return runner.run(suite)


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
    verbose: bool = False,
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
    os.environ["TANKBENCH_PATIENT_DIR"] = str(work.resolve())
    proc = subprocess.Popen(
        [sys.executable, str(work / "app.py")],
        cwd=str(work),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_health(url)
        alive = run_tests(url, repo_root() / "spec", verbose=verbose)
        rounds = run_tests(url, repo_root() / "rounds", verbose=verbose)

        measures_dir = repo_root() / "measures"
        if measures_dir.exists():
            measures = run_tests(url, measures_dir, verbose=verbose)
            measures_ran = measures.testsRun
            measures_passed = measures.testsRun - (len(measures.failures) + len(measures.errors))
            measure_failures = names_of(measures, "failures") + names_of(measures, "errors")
        else:
            measures_ran = 0
            measures_passed = 0
            measure_failures = []

        score = fold(
            alive_ran=alive.testsRun,
            alive_failed=len(alive.failures) + len(alive.errors),
            rounds_ran=rounds.testsRun,
            rounds_hits=rounds.testsRun - (len(rounds.failures) + len(rounds.errors)),
            measures_ran=measures_ran,
            measures_passed=measures_passed,
        )
        score.alive_failures = names_of(alive, "failures") + names_of(alive, "errors")
        score.round_misses = names_of(rounds, "failures") + names_of(rounds, "errors")
        score.measure_failures = measure_failures
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
    patch: Path | None = None,
    expect_baseline: bool = False,
    verbose: bool = False,
) -> Score:
    work = repo_root() / ".work" / ("baseline" if expect_baseline else "grade")
    copy_patient(work, overlay=overlay, app=app, patch=patch)
    return score_dir(work, expect_baseline=expect_baseline, verbose=verbose)

