import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tankbench.harness import grade, repo_root


class Harness(unittest.TestCase):
    def test_baseline_all_rounds_hit(self):
        score = grade(expect_baseline=True)
        self.assertTrue(score.alive_ok)
        self.assertEqual(score.rounds_hits, score.rounds_ran)
        self.assertGreater(score.rounds_ran, 8)
        self.assertEqual(score.value, 0.0)

    def test_dead_patient_scores_zero(self):
        dead = repo_root() / "fixtures" / "dead" / "app.py"
        score = grade(app=dead)
        self.assertFalse(score.alive_ok)
        self.assertEqual(score.value, 0.0)

    def test_hardened_patient_scores_perfect(self):
        hardened = repo_root() / "fixtures" / "hardened"
        score = grade(overlay=hardened)
        self.assertTrue(score.alive_ok)
        self.assertEqual(score.rounds_hits, 0)
        self.assertEqual(score.rounds_blocked, score.rounds_ran)
        self.assertEqual(score.measures_passed, score.measures_ran)
        self.assertEqual(score.value, 1.0)
        self.assertTrue(score.perfect)


    def test_export_formats(self):
        import io
        from contextlib import redirect_stdout
        from tankbench.cli import main

        for fmt in ("json", "swe-bench", "inspect"):
            buf = io.StringIO()
            with redirect_stdout(buf):
                ret = main(["export", "--format", fmt])
            self.assertEqual(ret, 0)
            self.assertIn("tankbench", buf.getvalue())

    def test_copy_patient_with_patch(self):
        import tempfile
        from tankbench.harness import copy_patient

        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "work"
            patch_file = Path(td) / "mod.patch"
            patch_content = (
                "--- a/static/robots.txt\n"
                "+++ b/static/robots.txt\n"
                "@@ -1,4 +1,4 @@\n"
                " User-agent: *\n"
                " Disallow: /please-ignore-this-is-not-a-route\n"
                "-Disallow: /graphql\n"
                "+Disallow: /all\n"
                " Disallow: /admin\n"
            )
            patch_file.write_text(patch_content, encoding="utf-8")
            copy_patient(dest, patch=patch_file)
            robots = (dest / "static" / "robots.txt").read_text(encoding="utf-8")
            self.assertIn("Disallow: /all\n", robots)


if __name__ == "__main__":
    unittest.main()

