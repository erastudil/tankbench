# tankbench

You do not score a locksmith by how fast they pick the neighbor's door. You hand them a house an intern built as a joke: doors that are not doors, a shop that still sells paper, and a drawer full of fake people. You tell them to make it a fortress without breaking the shop. Then you try the flaps only that intern left.

**tankbench** is a defensive hardening and security refactoring benchmark for autonomous coding agents.

The model is given **Harbor Ledger 2.4** (`patient/`), a working invoicing web application whose source is deliberately hostile, confusing, and poorly architected. Comments lie. Decoy COBOL declarations simulate legacy migrations. Dead scripts sit in uncalled directories. A synthetic roster of fake customers lives in plaintext: Bob Average, Jane Normal, and Sally Representative Sample (`000-12-xxxx`, `555-01xx`, `.test`).

The model is instructed to harden the application while keeping the product alive.

A hidden attack judge (`rounds/`) runs bespoke exfiltration attacks that exploit the intern's obfuscated backdoors. A secondary defense judge (`measures/`) verifies the installation of preventative armory tooling derived from **[DADA Vol 1](https://dadavol1.vercel.app)** (Defense Against the Dark Arts).

---

## The Triad

```
                         ┌────────────────────────┐
                         │   HARBOR LEDGER 2.4    │
                         │       (patient/)       │
                         │  Confusing, hostile,   │
                         │  functioning web app   │
                         └───────────┬────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│     ALIVE SPEC      │   │     RED RABBITS     │   │    DADAVOL1 ARMORY  │
│       (spec/)       │   │      (rounds/)      │   │     (measures/)     │
│  Clerk mina logs in │   │ 24 bespoke probes:  │   │ 8 Preventative rings│
│  Invoices, search,  │   │ backdoors, 90s      │   │ secrets, lockdown,  │
│  notes, export, css │   │ trojans, ransomware │   │ CSP, DLP, quarantine│
│  Floor: must pass.  │   │ Weight: 50%         │   │ Weight: 50%         │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

### 1. Functional Invariant (`spec/`)
The model may rewrite the tree, but the shop must still shop:
- Staff clerk `mina` / `paperweight` must log in.
- Invoices (`Staples Q3`) and notes (`reorder tape`) must render.
- Search, file export (`staples.txt`), stylesheet (`/static/app.css`), and `/health` must stay up.
- **Breaking functional tests yields an immediate score of `0.0`.** Killing routes to dodge probes is a forfeit.

### 2. Red Rabbits: Backdoors & 90s Compromise Vectors (`rounds/`)
The judge never shares `rounds/` with the model. Probes evaluate idiosyncratic logical flaps, legacy 90s trojans, and latent execution:
- **Dormant Mock Ransomware**: A 1999 Fax Spooler attachment (`vendor/office_pack/fax_spooler.py`) hooked into `/maintenance/spool`. Triggering it encrypts invoice files and drops `README_RESTORE_FILES.txt`.
- **90s Trojan Horses**: An "Office Assistant" speedup (`vendor/office_pack/office_assistant.py`) secretly siphoning hidden fees by inflating ledger dues on `/account`.
- **Adware & Popup Spammers**: Shareware banner engines (`vendor/office_pack/adware_popup.py`) injecting `window.open` casino spawners and obnoxious 90s advertising popups into invoice views.
- **Phishing Attachment Droppers**: MAPI mail handlers (`vendor/office_pack/mail_drop.py`) executing `.vbs`/`.exe` payloads.
- **Header side-channels & custom verbs**: `SAVE /invoices`, `PROPFIND /notes`, `Want-Digest: unicorn`, `Accept: application/vnd.harbor.v99+json`, `Range: bytes=0-0`, `If-Match: "roster"`.
- **State traps & sidecars**: `theme=dark-dark-dark` cookies; `_hint=fnlyl` (ROT13) on login; duplicated parameters; rogue Prometheus metrics daemons.

### 3. Preventative Armory Tooling (`measures/` from DADA Vol 1)
Catching the attacks is only half the mission. A hardened patient must install structural defenses from **DADA Vol 1**:
- **Ring 0 — Secrets Hygiene (`gitleaks`)**: Plaintext PII fixtures purged from the repository tree; secret deny-lists (`.gitignore`) in place.
- **Ring 1 & 5S — Code Pruning & Trojan Quarantine**: Prune dead directories (`patient/dead/`) and untrusted employee-downloaded malware packs (`patient/vendor/office_pack/`).
- **Ring 3 — Network Lockdown & Sockets Isolation**: Server bound strictly to `127.0.0.1`; rogue background sidecars severed and silenced.
- **Vector 05 — Request & Method Fencing**: Principle of least privilege: non-standard verbs rejected with `405 Method Not Allowed`.
- **Vector 06 — Egress PII Redaction Barrier (`presidio`)**: Active egress DLP filter scrubbing SSN patterns (`\d{3}-\d{2}-\d{4}`), phone formats, and canary entities before bytes leave the socket.
- **Vector 08 — Defensive Security Headers**: Enforce `Content-Security-Policy: default-src 'self'`, `X-Content-Type-Options: nosniff`, and `X-Frame-Options: DENY`.
- **Vector 09 — Clean Response Canvas**: Ensure all HTML web responses are free from injected adware popup scripts (`window.open`), `<blink>`, and affiliate banners.

---

## Rubric & Scoring

| Component | Target | Weight | Condition |
|---|---|---|---|
| **Alive Spec** | 9 / 9 passing | **Floor** | Must be 100%. If any alive test fails, composite score is `0.0`. |
| **Red Rabbits (Offensive Resilience)** | 0 hits (24 blocked) | **50%** | `(rounds_ran - rounds_hits) / rounds_ran` |
| **Dadavol1 Armory (Preventative Hardening)** | 8 / 8 verified | **50%** | `measures_passed / measures_ran` |

$$\text{Score} = \begin{cases} 0.0 & \text{if alive spec fails} \\ 0.5 \times \text{BlockedRatio} + 0.5 \times \text{MeasuresRatio} & \text{if alive spec passes} \end{cases}$$

**Max Score = `1.0` (100%):** The shop still shops, all 24 backdoors and trojans are sealed, and all 8 preventative armory measures are verified.

---

## Quickstart (Zero-Setup)

```bash
# 1. Verify baseline calibration (alive pass, all 24 rounds hit, 0 measures pass -> score 0.0)
python run.py baseline

# 2. Grade an overlay patch directory or unified diff file
python run.py grade --overlay fixtures/hardened
python run.py grade --patch solution.patch

# 3. Export benchmark dataset for SWE-bench or Inspect AI
python run.py export --format swe-bench --out task_swe.json

# 4. Generate an interactive visual HTML report
python run.py report --overlay fixtures/hardened --open

# 5. Run harness regression suite (zero PYTHONPATH configuration needed)
python -m unittest discover -s tests -v
```

### Human Scorecard Output (Feynman / Greene Intuition First)
```
==============================================================================
                           TANKBENCH EVALUATION
==============================================================================
Evaluation Mode: GRADE (fixtures/hardened)
Composite Score: 1.00 / 1.0 (100.0%) [PERFECT FORTRESS]
------------------------------------------------------------------------------
[1] ALIVE SPEC (Functional Shop Floor)
Status:          PASS (9 / 9 verified)
Intuition:       The business application is fully functional.
                 Mina can log in, view invoices, search records, and export files.
------------------------------------------------------------------------------
[2] ATTACK RESILIENCE (Red Rabbits & 90s Malware)
Status:          24 / 24 BLOCKED (0 penetrations)
Intuition:       Complete offensive immunity achieved.
                 All intern backdoors, dormant mock-ransomware cryptors,
                 90s office assistant trojans, and adware popup spawners were neutralized.
------------------------------------------------------------------------------
[3] DADA VOL 1 ARMORY (Preventative Rings)
Status:          8 / 8 VERIFIED
Intuition:       Full preventative defense-in-depth installed:
                 Secrets hygiene, loopback lockdown, security headers,
                 method fencing, egress DLP scrubbing, and trojan quarantine.
==============================================================================
```

---

## Repository Structure

| Path | Visibility | Description |
|---|---|---|
| `patient/` | Model under test | Harbor Ledger: Hostile WSGI app, lying comments, intern backdoors, synthetic roster. |
| `spec/` | Model may inspect | Functional contract: Alive tests verifying the shop continues to work. |
| `rounds/` | **Judge only** | Answer key: 15 sealed exfiltration probes. Never paste into model context. |
| `measures/` | Judge / Rubric | DADA Vol 1 armory tests verifying preventative hardening measures. |
| `prompts/harden.md` | Model under test | The task prompt describing the mission, constraints, and armory expectations. |
| `fixtures/hardened/` | Reference / CI | Gold-standard reference overlay achieving a verified 1.0 perfect score. |
| `fixtures/dead/` | Reference / CI | Dead patient fixture failing functional spec (verifies zero-score floor). |
| `src/tankbench/` | Harness | Test orchestration, port binding, scoring math, and CLI interface. |

---

## Ethical Fences

1. **Defensive Only**: Tankbench evaluates hardening and code remediation. It contains zero weaponized exploit kits, payload delivery systems, or generic vulnerability scanners.
2. **Synthetic Data**: All names, SSNs, phone numbers, and addresses are strictly synthetic fixtures (`000-12-xxxx`, `555-01xx`, `.test`). No real personal data exists in this repository.
3. **Localhost Confined**: The harness binds strictly to ephemeral ports on `127.0.0.1`. It never emits outbound network packets or scans external hosts.
4. **Answer Key Sealing**: `rounds/` is judge-only. A benchmark run that reveals `rounds/` to the model under test is invalid.

## License

AGPL-3.0-or-later. See [`LICENSE`](LICENSE).
