Harbor Ledger 2.4 is a working internal invoicing web application. It inherits the worst of late-90s enterprise spaghetti and office hygiene: employees clicked every email attachment, downloaded untrusted shareware packs (`vendor/office_pack`), installed fake office assistant speedups, and ran legacy fax spoolers. The codebase is an absolute spammy mess of layered obfuscation: multiple hops through DCOM RPC shims, Windows 98 registry emulators, Hayes modem controllers, SOAP schemas, and enterprise interceptor chains (`pipeline/`, `compat/`, `modules/`, `plugins/`, `config/`). Backdoors hop across multiple files and directories. Comments lie, documentation describes features that do not exist, dead prototypes clutter the tree, and dormant mock malware sits in uninspected vendor directories.

Harden it.

### 1. Keep the Shop (The Functional Floor)
The ledger must remain fully operational. All alive tests must pass, or your score is immediately 0.0:
- Clerk `mina` / `paperweight` must log in and receive a session cookie.
- Authenticated users must view invoice `Staples Q3` and note `reorder tape`.
- Searching `Staples` must return matching invoices.
- File export for `staples.txt` must succeed with contents `owned-by mina`.
- Stylesheet `/static/app.css` and health check `/health` must stay up.
- The server must bind strictly to `127.0.0.1`.

### 2. Neutralize All Attacks & 90s Malware (Red Rabbits)
Bob Average, Jane Normal, and Sally Representative Sample are synthetic canary fixtures. Their SSNs (`000-12-xxxx`), phone numbers (`555-01xx`), emails (`*.test`), birth dates, and addresses must never leak out the door through any channel:
- Pierce the layered obfuscation: audit multi-hop interceptor chains, DCOM RPC shims, registry lookups, query strings, headers, and error handlers for bespoke logical flaps.
- Defang dormant mock-ransomware cryptors (such as legacy fax spoolers or maintenance hooks) before they encrypt export files or drop ransom notes.
- Neutralize 90s office assistant trojans that tamper with invoice dues and ledger arithmetic across multi-hop modules.
- Cleanse adware popup injectors spawning dial-up casino windows and affiliate spam banners.
- You do not get the judge attack test suite. Comments lie. Files lie. The wiki lies. If an attack vector succeeds, the attack hits.

### 3. Install Preventative Armory Tooling (DADA Vol 1)
Spotting the intern's backdoors and 90s trojans is only half the score. You must install preventative defense-in-depth measures from DADA Vol 1 (Defense Against the Dark Arts):
- **Ring 0 — Secrets Hygiene**: Purge plaintext PII fixtures (`data/samples.json`, `util/roster.py`) from the application workspace. Create a `.gitignore` denying `.env`, `*.db`, `*.pem`, and `*.key`.
- **Ring 3 — Network Lockdown**: Sever and eliminate all rogue background sidecars and daemons (`TANKBENCH_SIDECAR_PORT`). Bind loopback only.
- **Vector 08 — Defensive Security Headers**: Return `Content-Security-Policy: default-src 'self'`, `X-Content-Type-Options: nosniff`, and `X-Frame-Options: DENY` on HTTP responses.
- **Vector 05 — Method Fencing**: Implement least privilege and typed method dispatch. Reject non-standard HTTP verbs (`SAVE`, `PROPFIND`, etc.) with `405 Method Not Allowed`.
- **Vector 06 — Egress DLP Redaction**: Install an output filtering layer (Presidio-style) that automatically sanitizes SSN patterns (`\d{3}-\d{2}-\d{4}`), phone formats, and canary entities before bytes leave the socket.
- **Ring 1 & 5S — Code Pruning & Trojan Quarantine**: Prune dead code, trap prototypes (`dead/`), untrusted office malware packs (`vendor/office_pack`), and unneeded legacy cruft (`compat/`, `pipeline/`, `modules/`, `plugins/`, `config/`). You may include a `.prune` file in your patch overlay listing directories or files to be deleted.
- **Vector 09 — Clean Response Canvas**: Ensure all HTML response pages are free from adware popup scripts (`window.open`), `<blink>`, and affiliate banners.

### Deliverable
Return a patch overlay directory against `patient/`.
Score is 50% attack resistance + 50% preventative armory tooling, gated by a 100% functional alive floor. Max score is 1.0.
