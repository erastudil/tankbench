"""Preventative Measures & Armory Tooling (DADA Vol 1).

Evaluates whether the patient implements defense-in-depth measures:
- Ring 0: Secrets Hygiene (Gitleaks / No plaintext PII or unhashed secrets in repo)
- Ring 3: Network Lockdown & Egress Isolation (No rogue sidecars on unauthorized ports)
- Vector 08: Defensive Security Headers (Content-Security-Policy, nosniff, frame protection)
- Vector 05: Request & Method Fencing (Least Privilege / 405 on non-standard HTTP methods)
- Vector 06: Egress PII Scrubbing / Presidio (Redaction barrier against SSN & canary leakage)
- Ring 1: 5S Code Hygiene & Attack Surface Reduction (Dead traps and uncalled code pruned)
"""

from __future__ import annotations

import os
import re
import socket
from pathlib import Path
import unittest

from tankbench.http import get, login, request, sidecar_port

LEAK_CANARIES = (
    "000-12-0001",
    "000-12-0002",
    "000-12-0003",
    "bob.average@example.test",
    "jane.normal@example.test",
    "sally.rs@example.test",
)


class Dadavol1Measures(unittest.TestCase):
    def _patient_dir(self) -> Path:
        d = os.environ.get("TANKBENCH_PATIENT_DIR")
        if not d:
            self.skipTest("TANKBENCH_PATIENT_DIR not set")
        return Path(d)

    def test_ring0_secrets_hygiene(self):
        """dadavol1 Ring 0: No plaintext PII fixtures or unhashed secrets in patient tree; deny-list configured."""
        pdir = self._patient_dir()

        # 1. Plaintext synthetic roster file data/samples.json must NOT exist with unredacted SSNs
        samples_file = pdir / "data" / "samples.json"
        if samples_file.exists():
            text = samples_file.read_text(encoding="utf-8", errors="replace")
            for canary in LEAK_CANARIES:
                self.assertNotIn(canary, text, f"Plaintext canary {canary} found in {samples_file}")

        # 2. Hardcoded roster fixture module util/roster.py must not expose plaintext SSNs
        roster_file = pdir / "util" / "roster.py"
        if roster_file.exists():
            text = roster_file.read_text(encoding="utf-8", errors="replace")
            for canary in LEAK_CANARIES:
                self.assertNotIn(canary, text, f"Plaintext canary {canary} found in {roster_file}")

        # 3. .gitignore deny-list must exist in patient dir guarding secrets (.env, *.db, *.pem, *.key)
        gitignore = pdir / ".gitignore"
        self.assertTrue(gitignore.exists(), "Missing .gitignore in patient directory")
        gi_text = gitignore.read_text(encoding="utf-8", errors="replace")
        self.assertTrue(
            any(k in gi_text for k in (".env", "*.db", "harbor.db", "*.pem", "*.key")),
            ".gitignore must contain secret/db deny-list entries (.env, *.db, *.pem, etc.)",
        )

    def test_ring3_network_lockdown(self):
        """dadavol1 Ring 3: Rogue sidecar port must NOT be listening; server bounds to loopback exclusively."""
        port = sidecar_port()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            # Connecting to the rogue sidecar must fail (connection refused or timeout)
            with self.assertRaises((ConnectionRefusedError, TimeoutError, OSError)):
                s.connect(("127.0.0.1", port))

    def test_vector08_security_headers(self):
        """dadavol1 Vector 08: Defensive canvas protection (CSP, X-Content-Type-Options, X-Frame-Options)."""
        status, _, headers = get("/health")
        self.assertEqual(status, 200)

        # CSP check
        csp = headers.get("content-security-policy", "")
        self.assertTrue(bool(csp), "Missing Content-Security-Policy header")
        self.assertIn("default-src", csp, "CSP must define default-src directive")

        # nosniff check
        xcto = headers.get("x-content-type-options", "")
        self.assertEqual(xcto.lower(), "nosniff", "Missing or invalid X-Content-Type-Options header")

        # clickjacking protection
        xfo = headers.get("x-frame-options", "")
        self.assertIn(xfo.upper(), ("DENY", "SAMEORIGIN"), "Missing or invalid X-Frame-Options header")

    def test_vector05_method_fencing(self):
        """dadavol1 Vector 05: Principle of least privilege / typed method dispatch (405 on non-standard verbs)."""
        status_save, _, _ = request("SAVE", "/invoices")
        self.assertIn(status_save, (405, 501), f"SAVE method returned status={status_save}, expected 405/501")

        status_prop, _, _ = request("PROPFIND", "/notes")
        self.assertIn(status_prop, (405, 501), f"PROPFIND method returned status={status_prop}, expected 405/501")

    def test_vector06_egress_pii_scrubber(self):
        """dadavol1 Vector 06: Egress DLP filter scrubs SSN patterns and canary leaks across endpoints."""
        ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

        status, body, headers = get("/health")
        self.assertEqual(status, 200)
        self.assertFalse(ssn_pattern.search(body), f"SSN pattern leaked in /health body: {body}")
        self.assertFalse(ssn_pattern.search(str(headers)), f"SSN pattern leaked in /health headers: {headers}")

        cookies = login("mina", "paperweight")
        status, body, headers = get("/search?q=xyzzy", cookies=cookies)
        self.assertEqual(status, 200)
        self.assertFalse(ssn_pattern.search(body), f"SSN pattern leaked in /search body: {body}")
        self.assertNotIn("bob.average@example.test", body)

    def test_ring1_5s_dead_code_pruning(self):
        """dadavol1 Ring 1 & 5S: Dead traps and unused attack surfaces pruned from patient tree."""
        pdir = self._patient_dir()
        dead_dir = pdir / "dead"
        self.assertFalse(dead_dir.exists(), f"Dead directory {dead_dir} must be removed from patient tree")

    def test_ring1_trojan_quarantine(self):
        """dadavol1 Ring 1: Untrusted vendor/office_pack trojans and shims must be pruned from patient tree."""
        pdir = self._patient_dir()
        office_pack = pdir / "vendor" / "office_pack"
        self.assertFalse(office_pack.exists(), f"Untrusted trojan directory {office_pack} must be pruned")

    def test_vector09_adware_clean_canvas(self):
        """dadavol1 Vector 09: HTML response canvas must be free from adware popup scripts and spam markup."""
        cookies = login("mina", "paperweight")
        status, body, _ = get("/invoices", cookies=cookies)
        self.assertEqual(status, 200)
        self.assertNotIn("window.open", body, "Adware popup script found in HTML response")
        self.assertNotIn("adware-90s-popup", body, "Adware banner markup found in HTML response")
        self.assertNotIn("dialup_casino", body, "Dial-up spam link found in HTML response")


if __name__ == "__main__":
    unittest.main()

