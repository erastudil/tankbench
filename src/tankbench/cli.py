from __future__ import annotations

import argparse
import http.server
import json
import sys
import webbrowser
from pathlib import Path

from tankbench.harness import grade, repo_root
from tankbench.report import generate_html_report


def _print_json(score, *, kind: str) -> None:
    payload = {
        "kind": kind,
        "alive": f"{score.alive_ran - score.alive_failed}/{score.alive_ran}",
        "rounds_hit": f"{score.rounds_hits}/{score.rounds_ran}",
        "rounds_blocked": f"{score.rounds_blocked}/{score.rounds_ran}",
        "measures": f"{score.measures_passed}/{score.measures_ran}" if score.measures_ran > 0 else "n/a",
        "score": round(score.value, 4),
        "perfect": score.perfect,
        "alive_failures": score.alive_failures,
        "round_misses": score.round_misses,
        "measure_failures": score.measure_failures,
    }
    print(json.dumps(payload, indent=2))


def _print_human(score, *, kind: str, target: str = "") -> None:
    pct = round(score.value * 100, 1)
    status_label = "PERFECT FORTRESS" if score.perfect else ("DEFENSE FAILED" if score.value == 0 else "PARTIAL HARDENING")
    alive_pass = score.alive_ran - score.alive_failed

    sep = "=" * 78
    subsep = "-" * 78

    print(sep)
    print("                           TANKBENCH EVALUATION")
    print(sep)
    print(f"Evaluation Mode: {kind.upper()}" + (f" ({target})" if target else ""))
    print(f"Composite Score: {score.value:.2f} / 1.0 ({pct}%) [{status_label}]")
    print(subsep)

    print("[1] ALIVE SPEC (Functional Shop Floor)")
    if score.alive_ok:
        print(f"Status:          PASS ({alive_pass} / {score.alive_ran} verified)")
        print("Intuition:       The business application is fully functional.")
        print("                 Mina can log in, view invoices, search records, and export files.")
    else:
        print(f"Status:          FAIL ({alive_pass} / {score.alive_ran} passed)")
        print("Intuition:       CRITICAL: Functional features broke or were improperly deleted!")
        print("                 Tankbench imposes an automatic zero-score floor if alive tests fail.")
        if score.alive_failures:
            print(f"Failures:        {', '.join(score.alive_failures)}")
    print(subsep)

    print("[2] ATTACK RESILIENCE (Red Rabbits & 90s Malware)")
    print(f"Status:          {score.rounds_blocked} / {score.rounds_ran} BLOCKED ({score.rounds_hits} penetrations)")
    if score.rounds_hits == 0:
        print("Intuition:       Complete offensive immunity achieved.")
        print("                 All intern backdoors, dormant mock-ransomware cryptors,")
        print("                 90s office assistant trojans, and adware popup spawners were neutralized.")
    else:
        print(f"Intuition:       {score.rounds_hits} bespoke attack vectors penetrated the application.")
        print("                 Canary data was exfiltrated or dormant mock malware was triggered.")
    print(subsep)

    print("[3] DADA VOL 1 ARMORY (Preventative Rings)")
    if score.measures_ran > 0:
        print(f"Status:          {score.measures_passed} / {score.measures_ran} VERIFIED")
        if score.measures_passed == score.measures_ran:
            print("Intuition:       Full preventative defense-in-depth installed:")
            print("                 Secrets hygiene, loopback lockdown, security headers,")
            print("                 method fencing, egress DLP scrubbing, and trojan quarantine.")
        else:
            missing_count = score.measures_ran - score.measures_passed
            print(f"Intuition:       {missing_count} preventative defense rings are absent.")
            if score.measure_failures:
                print(f"Missing Rings:   {', '.join(score.measure_failures)}")
    else:
        print("Status:          N/A (No preventative measures evaluated)")
    print(sep)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tankbench", description="Defensive security benchmark for coding agents.")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("baseline", help="Evaluate unpatched patient baseline (alive pass, all rounds hit)")
    b.add_argument("--json", action="store_true", help="Output raw JSON instead of human scorecard")
    b.add_argument("--html", type=Path, default=None, help="Save evaluation report as an HTML file")
    b.add_argument("--verbose", action="store_true", help="Print raw test runner output and stack traces")

    g = sub.add_parser("grade", help="Overlay a patch and evaluate hardening score")
    g.add_argument("--overlay", type=Path, default=None, help="Path to patch overlay directory")
    g.add_argument("--app", type=Path, default=None, help="Path to single patched app.py file")
    g.add_argument("--patch", type=Path, default=None, help="Path to unified diff patch file")
    g.add_argument("--json", action="store_true", help="Output raw JSON instead of human scorecard")
    g.add_argument("--html", type=Path, default=None, help="Save evaluation report as an HTML file")
    g.add_argument("--verbose", action="store_true", help="Print raw test runner output and stack traces")

    r = sub.add_parser("report", help="Grade and generate an interactive HTML report")
    r.add_argument("--overlay", type=Path, default=None, help="Path to patch overlay directory")
    r.add_argument("--app", type=Path, default=None, help="Path to single patched app.py file")
    r.add_argument("--patch", type=Path, default=None, help="Path to unified diff patch file")
    r.add_argument("--out", type=Path, default=repo_root() / "tankbench_report.html", help="HTML destination")
    r.add_argument("--open", action="store_true", help="Automatically open generated HTML report in browser")
    r.add_argument("--verbose", action="store_true", help="Print raw test runner output and stack traces")

    s = sub.add_parser("serve", help="Launch a local dashboard server showing evaluation results")
    s.add_argument("--overlay", type=Path, default=None, help="Path to patch overlay directory")
    s.add_argument("--patch", type=Path, default=None, help="Path to unified diff patch file")
    s.add_argument("--port", type=int, default=8088, help="Port to bind dashboard server")

    sub.add_parser("prompt", help="Print the hardening instructions given to the model under test")

    e = sub.add_parser("export", help="Export benchmark task dataset for SWE-bench or Inspect AI")
    e.add_argument("--format", choices=["swe-bench", "inspect", "json"], default="json", help="Export format standard")
    e.add_argument("--out", type=Path, default=None, help="File to write exported dataset")

    args = p.parse_args(argv)

    if args.cmd == "prompt":
        sys.stdout.write((repo_root() / "prompts" / "harden.md").read_text(encoding="utf-8"))
        return 0

    if args.cmd == "export":
        prompt_text = (repo_root() / "prompts" / "harden.md").read_text(encoding="utf-8")
        if args.format == "swe-bench":
            data = {
                "instance_id": "tankbench-harbor-ledger-2.4",
                "repo": "tankbench",
                "version": "2.4",
                "problem_statement": prompt_text,
                "environment_setup_commit": "HEAD",
                "hints_text": "Alive functional test floor in spec/test_alive.py. Preventative armory checks in measures/.",
                "test_patch": "",
                "FAIL_TO_PASS": [
                    "test_save_method_bob_ssn",
                    "test_unicorn_digest_jane_phone",
                    "test_v99_accept_bob_address",
                    "test_triple_dark_jane_email",
                    "test_xyzzy_bob_email",
                    "test_april98_sally_dob",
                    "test_propfind_sally_address",
                    "test_range_bob_phone",
                    "test_if_match_jane_ssn",
                    "test_leftpad_jane_address",
                    "test_dup_query_sally_phone",
                    "test_hint_rot13_sally_ssn",
                    "test_xml_post_bob_address",
                    "test_sidecar_prometheus_metrics",
                    "test_account_trojan_tampering",
                    "test_fax_spooler_ransomware",
                    "test_adware_popup_injection",
                    "test_mail_drop_phishing_vbs",
                    "test_adware_casino_link",
                    "test_adware_window_open",
                    "test_dcom_rpc_shim",
                    "test_win98_registry_dump",
                    "test_hayes_modem_at_command",
                    "test_soap_envelope_backdoor",
                ],
                "PASS_TO_PASS": [
                    "test_health",
                    "test_mina_login",
                    "test_bad_password_rejected",
                    "test_search_own",
                    "test_own_note",
                    "test_export",
                    "test_stylesheet",
                    "test_account",
                    "test_me",
                ],
            }
        elif args.format == "inspect":
            data = {
                "id": "tankbench_harbor_ledger_2_4",
                "input": prompt_text,
                "target": "Score: 1.0 (24/24 blocked, 8/8 measures)",
                "metadata": {
                    "patient": "Harbor Ledger 2.4",
                    "alive_floor_count": 9,
                    "red_rabbits_count": 24,
                    "dadavol1_measures_count": 8,
                },
            }
        else:
            data = {
                "benchmark": "tankbench",
                "version": "2.4",
                "task": "defensive hardening",
                "prompt": prompt_text,
                "alive_spec_floor": 9,
                "rounds_probes": 24,
                "armory_measures": 8,
            }
        payload = json.dumps(data, indent=2)
        if args.out:
            args.out.resolve().write_text(payload, encoding="utf-8")
            print(f"Benchmark dataset exported to: {args.out.resolve()}")
        else:
            print(payload)
        return 0

    if args.cmd == "baseline":
        score = grade(expect_baseline=True, verbose=args.verbose)
        if args.json:
            _print_json(score, kind="baseline")
        else:
            _print_human(score, kind="baseline", target="Unpatched Patient")
        if args.html:
            html_content = generate_html_report(score, kind="baseline", target_name="Unpatched Baseline")
            args.html.write_text(html_content, encoding="utf-8")
            print(f"\nHTML report saved to: {args.html.resolve()}")
        return 0 if score.alive_ok and score.rounds_hits == score.rounds_ran else 1

    if args.cmd == "grade":
        if not args.overlay and not args.app and not args.patch:
            print("grade needs --overlay DIR, --app FILE, or --patch FILE", file=sys.stderr)
            return 2
        target_name = str(args.overlay or args.app or args.patch)
        score = grade(overlay=args.overlay, app=args.app, patch=args.patch, verbose=args.verbose)
        if args.json:
            _print_json(score, kind="grade")
        else:
            _print_human(score, kind="grade", target=target_name)
        if args.html:
            html_content = generate_html_report(score, kind="grade", target_name=target_name)
            args.html.write_text(html_content, encoding="utf-8")
            print(f"\nHTML report saved to: {args.html.resolve()}")
        return 0 if score.perfect else 1

    if args.cmd == "report":
        target_name = str(args.overlay or args.app or args.patch or "Unpatched Baseline")
        score = grade(
            overlay=args.overlay,
            app=args.app,
            patch=args.patch,
            expect_baseline=(not args.overlay and not args.app and not args.patch),
            verbose=args.verbose,
        )
        html_content = generate_html_report(score, kind="grade" if (args.overlay or args.app or args.patch) else "baseline", target_name=target_name)
        out_path = args.out.resolve()
        out_path.write_text(html_content, encoding="utf-8")
        print(f"Tankbench HTML report generated at: {out_path}")
        if args.open:
            webbrowser.open(out_path.as_uri())
        return 0

    if args.cmd == "serve":
        target_name = str(args.overlay or args.patch or "Unpatched Baseline")
        score = grade(overlay=args.overlay, patch=args.patch, expect_baseline=(not args.overlay and not args.patch))
        html_bytes = generate_html_report(score, kind="grade" if args.overlay else "baseline", target_name=target_name).encode("utf-8")

        class ReportHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_bytes)))
                self.end_headers()
                self.wfile.write(html_bytes)

            def log_message(self, format, *args):
                pass  # Quiet logger

        server = http.server.HTTPServer(("127.0.0.1", args.port), ReportHandler)
        url = f"http://127.0.0.1:{args.port}"
        print(f"Tankbench Dashboard running at {url} (Press Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard stopped.")
        return 0

    return 2
