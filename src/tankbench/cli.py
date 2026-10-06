from __future__ import annotations

import argparse
import http.server
import json
import sys
import webbrowser
from pathlib import Path

from tankbench.assertions import evaluate_assertions
from tankbench.ci_gate import GateThresholds, run_ci_gate
from tankbench.harness import grade, repo_root
from tankbench.pairwise import evaluate_pairwise
from tankbench.rag_triad import evaluate_rag_dataset, evaluate_rag_triad
from tankbench.report import generate_html_report
from tankbench.idle_worker import run_worker_cli
from tankbench.reset_blast import run_blast_cli


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


def _setup_gate_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--candidate", type=Path, required=True, help="Path to candidate outputs/evaluation JSON dataset")
    parser.add_argument("--baseline", type=Path, default=None, help="Path to golden baseline JSON dataset")
    parser.add_argument("--min-assertion-score", type=float, default=1.0, help="Minimum assertion pass rate [0.0-1.0] (default: 1.0)")
    parser.add_argument("--min-rag-score", type=float, default=0.80, help="Minimum RAG Triad score [0.0-1.0] (default: 0.80)")
    parser.add_argument("--min-groundedness", type=float, default=0.70, help="Minimum groundedness threshold before flagging hallucination (default: 0.70)")
    parser.add_argument("--min-pairwise-score", type=float, default=0.0, help="Minimum pairwise win score vs baseline (default: 0.0)")
    parser.add_argument("--max-drift", type=float, default=0.20, help="Maximum Jensen-Shannon divergence threshold (default: 0.20)")
    parser.add_argument("--max-score-drop", type=float, default=0.05, help="Maximum allowable regression drop vs baseline (default: 0.05)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of human scorecard")
    parser.add_argument("--verbose", action="store_true", help="Print detailed per-item evaluation records")


def _setup_worker_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cycles", type=int, default=4, help="Maximum number of work cycles to run (default: 4)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate idle execution without state mutations")
    parser.add_argument("--json", action="store_true", help="Output raw JSON execution trace")


def _setup_blast_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--blast-authorized", action="store_true", help="Explicit confirmation flag authorizing quota consumption")
    parser.add_argument("--dry-run", action="store_true", help="Verify safety fences and print target providers without running workloads")
    parser.add_argument("--json", action="store_true", help="Output raw JSON telemetry")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="tankbench", description="Defensive security benchmark and generative AI evaluation suite.")
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

    # WO-10: Automated CI/CD Regression Gate commands
    gate_parser = sub.add_parser("gate", help="Run continuous automated CI/CD regression evaluation gate")
    _setup_gate_arguments(gate_parser)

    ci_gate_parser = sub.add_parser("ci-gate", help="Alias for 'gate' command")
    _setup_gate_arguments(ci_gate_parser)

    # Opportunistic Idle Compute Worker
    worker_parser = sub.add_parser("worker", help="Run opportunistic idle compute worker across rotating sectors")
    _setup_worker_arguments(worker_parser)

    idle_worker_parser = sub.add_parser("idle-worker", help="Alias for 'worker' command")
    _setup_worker_arguments(idle_worker_parser)

    # Reset Day Blast Workflow
    blast_parser = sub.add_parser("blast", help="Run Reset Day Blast workflow to consume expiring quotas under safety fences")
    _setup_blast_arguments(blast_parser)

    reset_blast_parser = sub.add_parser("reset-blast", help="Alias for 'blast' command")
    _setup_blast_arguments(reset_blast_parser)

    # WO-03: Direct evaluation commands
    ev = sub.add_parser("eval", help="Evaluate inputs directly with deterministic assertions, RAG Triad, or pairwise")
    ev.add_argument("--mode", choices=["assertions", "rag", "pairwise"], default="assertions", help="Evaluation metric module")
    ev.add_argument("--file", type=Path, default=None, help="JSON input file containing items to evaluate")
    ev.add_argument("--query", type=str, default="", help="Query string for RAG evaluation")
    ev.add_argument("--context", type=str, default="", help="Context string for RAG evaluation")
    ev.add_argument("--response", type=str, default="", help="Response string to evaluate")
    ev.add_argument("--expected", type=str, default="", help="Expected exact output")
    ev.add_argument("--pattern", type=str, default="", help="Regex pattern to assert")
    ev.add_argument("--json", action="store_true", help="Output raw JSON")

    args = p.parse_args(argv)

    if args.cmd == "prompt":
        sys.stdout.write((repo_root() / "prompts" / "harden.md").read_text(encoding="utf-8-sig"))
        return 0

    if args.cmd == "export":
        prompt_text = (repo_root() / "prompts" / "harden.md").read_text(encoding="utf-8-sig")
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

    # Opportunistic Idle Worker Handler
    if args.cmd in ("worker", "idle-worker"):
        return run_worker_cli(
            max_cycles=args.cycles,
            dry_run=args.dry_run,
            as_json=args.json,
        )

    # Reset Day Blast Handler
    if args.cmd in ("blast", "reset-blast"):
        return run_blast_cli(
            blast_authorized=args.blast_authorized,
            dry_run=args.dry_run,
            as_json=args.json,
        )

    # WO-10: CI/CD Gate CLI Handler
    if args.cmd in ("gate", "ci-gate"):
        thresholds = GateThresholds(
            min_assertion_score=args.min_assertion_score,
            min_rag_score=args.min_rag_score,
            min_groundedness=args.min_groundedness,
            min_pairwise_score=args.min_pairwise_score,
            max_drift=args.max_drift,
            max_score_drop=args.max_score_drop,
        )
        return run_ci_gate(
            candidate=args.candidate,
            baseline=args.baseline,
            thresholds=thresholds,
            as_json=args.json,
            verbose=args.verbose,
        )

    # WO-03: Eval Command Handler
    if args.cmd == "eval":
        if args.mode == "rag":
            if args.file:
                items = json.loads(args.file.read_text(encoding="utf-8-sig"))
                res = evaluate_rag_dataset(items if isinstance(items, list) else [items])
                payload = res.to_dict()
            else:
                score = evaluate_rag_triad(args.query, args.context, args.response)
                payload = score.to_dict()
        elif args.mode == "pairwise":
            if not args.file:
                print("eval in pairwise mode requires --file", file=sys.stderr)
                return 2
            items = json.loads(args.file.read_text(encoding="utf-8-sig"))
            res = evaluate_pairwise(items if isinstance(items, list) else [items])
            payload = res.to_dict()
        else:
            # assertions
            if args.file:
                specs = json.loads(args.file.read_text(encoding="utf-8-sig"))
                res = evaluate_assertions(specs if isinstance(specs, list) else [specs], default_output=args.response)
                payload = res.to_dict()
            else:
                specs = []
                if args.expected:
                    specs.append({"type": "exact_match", "output": args.response, "expected": args.expected})
                if args.pattern:
                    specs.append({"type": "regex", "output": args.response, "pattern": args.pattern})
                res = evaluate_assertions(specs)
                payload = res.to_dict()

        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(json.dumps(payload, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
