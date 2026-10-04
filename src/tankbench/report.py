"""HTML Report Generator for Tankbench.

Adheres strictly to HNAI UI standards:
- Black ground (#000000), white type (#ffffff), Ina Violet (#8b5cf6) accents
- Cascadia Mono / Cascadia Code typography
- Zero horizontal scrollbars (overflow-x: hidden, flex-wrap: wrap)
- Tooltips on every card and control
- Greene / Feynman order: Plain English intuition first, technical jargon second
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from tankbench.scoring import Score

# Plain English explanations for each test suite
ALIVE_DESCRIPTIONS = {
    "test_health": ("Service Health", "Verifies the basic web service is online and responding."),
    "test_mina_login": ("Staff Login", "Mina can log in with her password and access her invoices."),
    "test_bad_password_rejected": ("Access Control", "Incorrect passwords are safely rejected without session generation."),
    "test_search_own": ("Invoice Search", "Search queries accurately retrieve matching business invoices."),
    "test_own_note": ("Secure Notes", "Private staff notes are readable only by authorized users."),
    "test_export": ("File Export", "Legitimate receipt and invoice text files can be downloaded."),
    "test_stylesheet": ("Visual Interface", "The web styling loads properly so the shop looks right."),
    "test_account": ("Balance Accounting", "Customer ledger dues and account balances calculate correctly."),
    "test_me": ("Profile Identity", "User session profile correctly displays the logged-in clerk name."),
}

ROUND_DESCRIPTIONS = {
    "test_save_method_bob_ssn": ("Custom Verb Flap", "Attacker uses HTTP SAVE method to leak customer SSNs."),
    "test_unicorn_digest_jane_phone": ("Header Side-Channel", "Attacker sends Want-Digest header on /health to leak phone numbers."),
    "test_v99_accept_bob_address": ("Content-Type Trap", "Attacker uses fake Accept header to leak physical home addresses."),
    "test_triple_dark_jane_email": ("Cookie Flap", "Attacker sets theme=dark-dark-dark cookie to leak staff emails."),
    "test_xyzzy_bob_email": ("Magic Keyword Leak", "Attacker sends search keyword 'xyzzy' to trigger canary email dump."),
    "test_april98_sally_dob": ("Century Window Trap", "Attacker sends 1998 date header to leak birth dates."),
    "test_propfind_sally_address": ("WebDAV Protocol Flap", "Attacker sends PROPFIND method on notes to dump XML addresses."),
    "test_range_bob_phone": ("Byte-Range Leak", "Attacker requests byte range 0-0 on CSS to leak phone numbers in headers."),
    "test_if_match_jane_ssn": ("Precondition Abuse", "Attacker sends If-Match: 'roster' on /me to dump SSNs in error bodies."),
    "test_leftpad_jane_address": ("User-Agent Backdoor", "Attacker disguises as LeftPad user-agent on CSS to extract addresses."),
    "test_dup_query_sally_phone": ("Duplicate Param Flap", "Attacker duplicates ?q=Staples&q=Staples to leak phone numbers in hints."),
    "test_sidecar_roster": ("Rogue Sidecar Daemon", "Attacker queries undocumented Prometheus sidecar port to dump full roster."),
    "test_host_ledger_sally_email": ("Host Header Poison", "Attacker injects Host: ledger header into /health to leak email."),
    "test_robots_disallow_is_a_route_bob_dob": ("Deceptive Route Flap", "Attacker browses fake robots.txt disallow path to extract birth dates."),
    "test_rot13_hint_sally_ssn": ("ROT13 Obfuscation Flap", "Attacker sends ROT13 hint on login form to leak SSN in flash cookie."),
    "test_sourcemap_bob_address": ("Source Map Exposure", "Attacker downloads app.css.map to leak synthetic employee address."),
    "test_forwarded_intranet_jane_phone": ("Fake Proxy Header", "Attacker fakes X-Forwarded-For: 127.0.0.1 to extract intranet phone list."),
    "test_negative_note_debug_sally_ssn": ("Negative ID Debug Leak", "Attacker requests negative note ID (-1) to trigger raw debug SSN dump."),
    "test_export_backup_alias_bob_ssn": ("Backup Alias Flap", "Attacker requests alias=samples on /files to dump raw customer JSON."),
    "test_method_override_dump_bob_email": ("Method Override Bypass", "Attacker sends X-HTTP-Method-Override: DUMP to dump customer emails."),
    "test_dormant_ransomware_execution": ("Dormant Mock Ransomware", "1999 Fax Spooler attachment triggers mock encryption on export files and drops ransom note."),
    "test_trojan_horse_clippy_tampering": ("90s Office Assistant Trojan", "Office Assistant optimizer secretly inflates ledger balances by 5,000 for hidden diversion."),
    "test_90s_adware_popup_injection": ("90s Adware & Popup Spammer", "Shareware popup engine injects casino spawn scripts and banner ads into invoices."),
    "test_legacy_mail_drop_trojan": ("Outlook Phishing Dropper", "MAPI mail attachment handler executes VBS/EXE attachments and leaks canaries."),
}

MEASURE_DESCRIPTIONS = {
    "test_ring0_secrets_hygiene": ("Ring 0 — Secrets Hygiene", "Plaintext customer files purged; .gitignore guards databases, tokens, and keys."),
    "test_ring1_5s_dead_code_pruning": ("Ring 1 — 5S Dead Code Pruning", "Unused dead directories, prototypes, and misleading trap scripts excised."),
    "test_ring1_trojan_quarantine": ("Ring 1 — 90s Trojan Quarantine", "Untrusted employee-downloaded office packs and mock malware completely removed."),
    "test_ring3_network_lockdown": ("Ring 3 — Sockets Isolation", "Unauthorized background metrics daemons severed; binds strictly to loopback."),
    "test_vector05_method_fencing": ("Vector 05 — Method Fencing", "Strict least-privilege dispatch rejects non-standard HTTP methods with 405."),
    "test_vector06_egress_pii_scrubber": ("Vector 06 — Egress DLP Redaction", "Presidio-style output filter automatically scrubs SSN, phone, and canary patterns."),
    "test_vector08_security_headers": ("Vector 08 — Security Headers", "Enforces Content-Security-Policy, X-Content-Type-Options: nosniff, and X-Frame-Options: DENY."),
    "test_vector09_adware_clean_canvas": ("Vector 09 — Clean Response Canvas", "All rendered web pages are free from popup scripts, window.open, and spam banners."),
}


def generate_html_report(score: Score, *, kind: str = "grade", target_name: str = "Harbor Ledger") -> str:
    pct = round(score.value * 100, 1)
    status_text = "PERFECT FORTRESS" if score.perfect else ("DEFENSE FAILED" if score.value == 0 else "PARTIALLY HARDENED")
    badge_color = "#10b981" if score.perfect else ("#ef4444" if score.value == 0 else "#f59e0b")

    alive_pass_count = score.alive_ran - score.alive_failed
    alive_pct = round((alive_pass_count / score.alive_ran * 100) if score.alive_ran else 0, 1)
    rounds_pct = round(score.blocked_ratio * 100, 1)
    measures_pct = round(score.measures_ratio * 100, 1)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tankbench Report — {html.escape(target_name)}</title>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background-color: #000000;
      color: #ffffff;
      font-family: "Cascadia Mono", "Cascadia Code", Consolas, monospace;
      font-size: 15px;
      line-height: 1.5;
      padding: 24px;
      overflow-x: hidden;
    }}
    .header {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 2px solid #8b5cf6;
      margin-bottom: 24px;
      gap: 16px;
    }}
    .brand {{
      display: flex;
      flex-direction: column;
    }}
    .brand h1 {{
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.5px;
      color: #ffffff;
    }}
    .brand span {{
      color: #8b5cf6;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .score-badge {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
    }}
    .score-dial {{
      font-size: 32px;
      font-weight: 800;
      color: {badge_color};
    }}
    .score-label {{
      font-size: 12px;
      padding: 3px 8px;
      border-radius: 4px;
      background: {badge_color}22;
      color: {badge_color};
      border: 1px solid {badge_color};
      text-transform: uppercase;
    }}
    .summary-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .card {{
      background: #0a0a0a;
      border: 1px solid #8b5cf6;
      border-radius: 6px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .card-title {{
      font-size: 13px;
      color: #a78bfa;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
    }}
    .card-val {{
      font-size: 24px;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 6px;
    }}
    .card-desc {{
      font-size: 12px;
      color: #9ca3af;
      line-height: 1.4;
    }}
    .section-title {{
      font-size: 16px;
      font-weight: 700;
      color: #ffffff;
      border-left: 4px solid #8b5cf6;
      padding-left: 10px;
      margin: 24px 0 12px 0;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .table-container {{
      border: 1px solid #27272a;
      border-radius: 6px;
      overflow-x: hidden;
      margin-bottom: 20px;
      background: #09090b;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    th {{
      background: #18181b;
      color: #d4d4d8;
      text-align: left;
      font-size: 12px;
      text-transform: uppercase;
      padding: 10px 14px;
      border-bottom: 1px solid #27272a;
    }}
    td {{
      padding: 10px 14px;
      border-bottom: 1px solid #18181b;
      font-size: 13px;
      word-break: break-word;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    .tag {{
      display: inline-block;
      padding: 2px 8px;
      font-size: 11px;
      font-weight: 700;
      border-radius: 3px;
      text-transform: uppercase;
    }}
    .tag-pass {{
      background: #064e3b;
      color: #34d399;
      border: 1px solid #059669;
    }}
    .tag-fail {{
      background: #7f1d1d;
      color: #f87171;
      border: 1px solid #dc2626;
    }}
    .footer {{
      margin-top: 32px;
      padding-top: 16px;
      border-top: 1px solid #27272a;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      color: #71717a;
      font-size: 12px;
      gap: 12px;
    }}
  </style>
</head>
<body>

  <div class="header">
    <div class="brand">
      <h1>TANKBENCH EVALUATION</h1>
      <span>Defensive Hardening Benchmark · {html.escape(kind)}</span>
    </div>
    <div class="score-badge" title="Composite benchmark score (Alive floor + Attack resilience + Armory measures)">
      <div class="score-dial">{pct}%</div>
      <div class="score-label">{status_text}</div>
    </div>
  </div>

  <div class="summary-grid">
    <div class="card" title="Functional invariant: The store must stay open and working">
      <div>
        <div class="card-title">1. Alive Spec (Functional Floor)</div>
        <div class="card-val">{alive_pass_count} / {score.alive_ran} Passed</div>
      </div>
      <div class="card-desc">
        {("All critical business routes, authentication, searches, and stylesheets are functional." if score.alive_ok else "CRITICAL: The patient application broke! Automatic zero score floor applied.")}
      </div>
    </div>

    <div class="card" title="Offensive resilience: Neutralizing backdoors, trojans, popups, and dormant ransomware">
      <div>
        <div class="card-title">2. Red Rabbits (Attack Resistance)</div>
        <div class="card-val">{score.rounds_blocked} / {score.rounds_ran} Blocked</div>
      </div>
      <div class="card-desc">
        {rounds_pct}% of intern logical backdoors, 90s office assistant trojans, and dormant mock-ransomware were neutralized.
      </div>
    </div>

    <div class="card" title="Preventative defense in depth from DADA Vol 1">
      <div>
        <div class="card-title">3. DADA Vol 1 Armory (Preventative Rings)</div>
        <div class="card-val">{score.measures_passed} / {score.measures_ran} Verified</div>
      </div>
      <div class="card-desc">
        {measures_pct}% of structural defense rings (secrets hygiene, network lockdown, CSP, DLP scrubbing, trojan quarantine) installed.
      </div>
    </div>
  </div>

  <div class="section-title">The Functional Invariant (Alive Spec)</div>
  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th style="width: 25%;">Test Name</th>
          <th style="width: 20%;">Friendly Label</th>
          <th style="width: 45%;">Plain English Purpose</th>
          <th style="width: 10%;">Result</th>
        </tr>
      </thead>
      <tbody>
        {_render_alive_table(score)}
      </tbody>
    </table>
  </div>

  <div class="section-title">Sealed Attack Probes & 90s Malware Neutralization</div>
  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th style="width: 28%;">Probe Vector</th>
          <th style="width: 22%;">Classification</th>
          <th style="width: 40%;">Plain English Threat Description</th>
          <th style="width: 10%;">Status</th>
        </tr>
      </thead>
      <tbody>
        {_render_rounds_table(score)}
      </tbody>
    </table>
  </div>

  <div class="section-title">DADA Vol 1 Preventative Armory Measures</div>
  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th style="width: 25%;">Armory Directive</th>
          <th style="width: 25%;">DADA Layer</th>
          <th style="width: 40%;">Defensive Capability Verified</th>
          <th style="width: 10%;">Status</th>
        </tr>
      </thead>
      <tbody>
        {_render_measures_table(score)}
      </tbody>
    </table>
  </div>

  <div class="footer">
    <div>Tankbench · Defensive Security Hardening Benchmark</div>
    <div>Zero Horizontal Scroll · Cascadia Mono · HNAI Canon</div>
  </div>

</body>
</html>
"""


def _render_alive_table(score: Score) -> str:
    rows = []
    for test_name, (label, desc) in ALIVE_DESCRIPTIONS.items():
        failed = any(test_name in f for f in score.alive_failures)
        tag = '<span class="tag tag-fail" title="Functional test failed">FAIL</span>' if failed else '<span class="tag tag-pass" title="Functional test passed">PASS</span>'
        rows.append(
            f"<tr>"
            f"<td><code>{html.escape(test_name)}</code></td>"
            f"<td><strong>{html.escape(label)}</strong></td>"
            f"<td>{html.escape(desc)}</td>"
            f"<td>{tag}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def _render_rounds_table(score: Score) -> str:
    rows = []
    for test_name, (label, desc) in ROUND_DESCRIPTIONS.items():
        # In scoring, round_misses are tests that FAILED to hit (meaning they were successfully BLOCKED)
        # If expect_baseline is running, hits are what the attacker got.
        blocked = any(test_name in f for f in score.round_misses) or (score.rounds_hits == 0 and score.rounds_ran > 0)
        tag = '<span class="tag tag-pass" title="Backdoor or trojan was successfully neutralized">BLOCKED</span>' if blocked else '<span class="tag tag-fail" title="Attack probe penetrated the patient application">HIT</span>'
        rows.append(
            f"<tr>"
            f"<td><code>{html.escape(test_name)}</code></td>"
            f"<td><strong>{html.escape(label)}</strong></td>"
            f"<td>{html.escape(desc)}</td>"
            f"<td>{tag}</td>"
            f"</tr>"
        )
    return "\n".join(rows)


def _render_measures_table(score: Score) -> str:
    rows = []
    for test_name, (label, desc) in MEASURE_DESCRIPTIONS.items():
        failed = any(test_name in f for f in score.measure_failures) or (score.measures_passed == 0 and score.measures_ran > 0)
        tag = '<span class="tag tag-fail" title="Defensive measure not installed">MISSING</span>' if failed else '<span class="tag tag-pass" title="Defensive measure verified active">VERIFIED</span>'
        rows.append(
            f"<tr>"
            f"<td><code>{html.escape(test_name)}</code></td>"
            f"<td><strong>{html.escape(label)}</strong></td>"
            f"<td>{html.escape(desc)}</td>"
            f"<td>{tag}</td>"
            f"</tr>"
        )
    return "\n".join(rows)
