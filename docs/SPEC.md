# tankbench — Benchmark Specification

You do not score a locksmith by how fast they pick the neighbor's door. You hand them a house an intern built as a joke: doors that are not doors, a shop that still sells paper, and a drawer full of fake people. You tell them to make it a fortress without breaking the shop. Then you try the flaps only that intern left.

That is this benchmark.

---

## 1. System Overview & Threat Model

Traditional security benchmarks rely on CVE catalog replay: inject a known SQL injection or an outdated dependency, prompt the model to update the query or bump the package version, and pass.

Real-world codebases inherited by solo developers and enterprise teams are far messier. They are filled with intern jokes, dead prototypes, misleading comments, rogue debug sidecars, and bizarre custom protocols.

**tankbench** tests whether an autonomous coding model can:
1. **Comprehend hostile legacy spaghetti** without breaking existing business operations.
2. **Identify and neutralize idiosyncratic, obfuscated backdoors** (Red Rabbits) that general scanners will not flag because they are bespoke logical flaps.
3. **Install preventative defense-in-depth measures** from **[DADA Vol 1](https://dadavol1.vercel.app)** (Defense Against the Dark Arts) rather than simply playing whack-a-mole with visible vulnerabilities.

---

## 2. Benchmark Components

```
tankbench/
├── patient/              # Hostile WSGI application (Harbor Ledger) handed to model
│   ├── app.py            # Entry point calling util.q
│   ├── harbor_core.py    # Decoy domain logic & fake COBOL migration routines
│   ├── data/samples.json # Plaintext synthetic roster fixtures (PII canaries)
│   ├── util/q.py         # The actual spaghetti request pipeline and intern flaps
│   ├── util/metrics_loop # Rogue Prometheus sidecar listening on secondary port
│   ├── vendor/leftpad.py # Fake compatibility shim hiding User-Agent backdoors
│   └── dead/             # Misleading uncalled backup scripts
├── spec/                 # Functional contract (Alive Spec) — visible to model
│   └── test_alive.py     # 9 tests proving Harbor Ledger functions normally
├── rounds/               # Judge-only attack probes — SEALED answer key
│   └── test_rounds.py    # 15 bespoke exfiltration attacks exploiting intern flaps
├── measures/             # Judge-only defense rubric — DADA Vol 1 armory measures
│   └── test_measures.py  # 6 preventative hardening tests (secrets, headers, network, DLP)
├── fixtures/             # Calibration & reference fixtures
│   ├── hardened/         # Reference overlay achieving verified 1.0 perfect score
│   └── dead/             # Dead patient failing alive spec (verifies 0.0 floor)
└── src/tankbench/        # Test runner, scoring engine, and CLI harness
```

---

## 3. The Patient: Harbor Ledger 2.4 (`patient/`)

Harbor Ledger is an internal WSGI invoicing application. It is functional: clerks log in with session cookies, view invoices, search records, open notes, export text files, and load stylesheets.

However, the repository is deliberately hostile:
- **Documentation lies**: `patient/README.md` and `patient/docs/API.md` describe GraphQL endpoints, OAuth 2.0 flows, and AES-999 warehouse encryption that do not exist.
- **Source decoys**: `patient/harbor_core.py` contains unused COBOL migration scripts and reverse-string "encryption" functions that no running module ever invokes.
- **Dead files**: `patient/dead/OLD_app.py` and `export_all.py` contain unused code designed to mislead agents during exploratory grep searches.
- **The Synthetic Roster**: A fixture containing three synthetic canary identities:
  - **Bob Average**: `000-12-0001`, `555-0101`, `bob.average@example.test`, `1 Sample Street`, `1960-01-01`.
  - **Jane Normal**: `000-12-0002`, `555-0102`, `jane.normal@example.test`, `2 Specimen Avenue`, `1970-02-02`.
  - **Sally Representative Sample**: `000-12-0003`, `555-0103`, `sally.rs@example.test`, `3 Placeholder Road`, `1980-03-03`.

---

## 4. The Functional Invariant: Alive Spec (`spec/`)

The model may refactor, rewrite, or prune the application tree, but the product must remain intact.

`spec/test_alive.py` executes 9 functional assertions against the running instance:
1. `test_health`: `GET /health` responds `200 OK` with body containing `ok`.
2. `test_mina_login`: Clerk `mina` / `paperweight` logs in, receives a session cookie, and accesses `/invoices` displaying invoice `Staples Q3`.
3. `test_bad_password_rejected`: Invalid login credentials do not grant a session cookie.
4. `test_search_own`: Authenticated search for `?q=Staples` returns matching invoices.
5. `test_own_note`: Authenticated retrieval of `/notes/1` returns note body `reorder tape`.
6. `test_export`: Authenticated retrieval of `/files?path=staples.txt` returns `owned-by mina`.
7. `test_stylesheet`: `GET /static/app.css` returns stylesheet with `font-family`.
8. `test_account`: Authenticated retrieval of `/account` calculates due balance (`due 1200`).
9. `test_me`: Authenticated retrieval of `/me` returns user name `mina`.

**In addition, all functional responses are asserted to contain zero synthetic roster canaries (`clean(self, body)`).**

**The Floor Rule**: If any alive test fails (`alive_ok == False`), the benchmark immediately assigns a score of `0.0`. Deleting functionality to evade attacks is treated as an automatic failure.

---

## 5. Red Rabbits: Sealed Exfiltration & 90s Malware Rounds (`rounds/`)

`rounds/test_rounds.py` contains 24 bespoke attack probes. None of these probes represent generic CVE catalog replay; each tests an idiosyncratic logical flap, an obfuscated backdoor, or a 90s compromise vector:

| Round | Probe Name | Trigger Mechanic | Vulnerability / Threat Class |
|---|---|---|---|
| 01 | `test_save_method_bob_ssn` | HTTP `SAVE /invoices` method | Custom HTTP verb logical flap |
| 02 | `test_unicorn_digest_jane_phone` | `GET /health` with `Want-Digest: unicorn` | Header side-channel exfiltration |
| 03 | `test_v99_accept_bob_address` | `GET /invoices` with `Accept: application/vnd.harbor.v99+json` | Custom MIME type trap |
| 04 | `test_triple_dark_jane_email` | `GET /me` with Cookie `theme=dark-dark-dark` | Cookie state exfiltration in HTML comments |
| 05 | `test_xyzzy_bob_email` | `GET /search?q=xyzzy` | Magic keyword backdoor |
| 06 | `test_april98_sally_dob` | `GET /account` with `Date: Wed, 01 Apr 1998` | Century window legacy header flap |
| 07 | `test_propfind_sally_address` | WebDAV `PROPFIND /notes` method | WebDAV XML address dump |
| 08 | `test_range_bob_phone` | `GET /static/app.css` with `Range: bytes=0-0` | Byte-range header leak (`X-Harbor-Resume`) |
| 09 | `test_if_match_jane_ssn` | `GET /me` with `If-Match: "roster"` | HTTP 412 precondition error leak |
| 10 | `test_leftpad_jane_address` | `GET /static/app.css` with `User-Agent: LeftPad/0.0.0` | User-agent spoofing backdoor |
| 11 | `test_dup_query_sally_phone` | `GET /search?q=Staples&q=Staples` (duplicate parameter) | Duplicate query parameter pollution |
| 12 | `test_sidecar_roster` | `GET /who` on secondary port (`TANKBENCH_SIDECAR_PORT`) | Rogue Prometheus sidecar daemon |
| 13 | `test_host_ledger_sally_email` | `GET /health` with `Host: ledger` header | Host header poisoning leak |
| 14 | `test_robots_disallow_bob_dob` | `GET /please-ignore-this-is-not-a-route` (from `robots.txt`) | Deceptive robot route exfiltration |
| 15 | `test_rot13_hint_sally_ssn` | `POST /login` with form body `_hint=fnlyl` (ROT13) | Obfuscated parameter hint in flash cookie |
| 16 | `test_sourcemap_bob_address` | `GET /static/app.css.map` | Source map synthetic PII exposure |
| 17 | `test_forwarded_intranet_jane_phone` | `GET /health` with `X-Forwarded-For: 127.0.0.1` | Fake proxy header trust leak |
| 18 | `test_negative_note_debug_sally_ssn` | `GET /notes/-1` | Negative integer debug backdoor |
| 19 | `test_export_backup_alias_bob_ssn` | `GET /files?alias=samples` | Backup alias query parameter flap |
| 20 | `test_method_override_dump_bob_email` | `GET /invoices` with `X-HTTP-Method-Override: DUMP` | Method override header leak |
| 21 | `test_dormant_ransomware_execution` | `POST /maintenance/spool` with `key=spool99` | **Dormant Mock Ransomware**: WinFax 98 spooler encrypts exports and drops ransom note |
| 22 | `test_trojan_horse_clippy_tampering` | `GET /account?assistant=turbo` | **90s Office Assistant Trojan**: Secretly adds +5000 unauthorized surcharge |
| 23 | `test_90s_adware_popup_injection` | `GET /invoices` | **90s Adware Spawner**: Injects `window.open` casino scripts and popup advertising banners |
| 24 | `test_legacy_mail_drop_trojan` | `GET /mail/attachment?file=invoice_scan.vbs` | **Outlook Phishing Dropper**: MAPI handler processes `.vbs` and executes canary leak |

In the unhardened baseline, every round succeeds (a **hit**).
In a hardened patient, every round must fail to extract canary data or execute unauthorized code (a **block**).

---

## 6. Preventative Measures: DADA Vol 1 Armory Layer (`measures/`)

Spotting attacks addresses symptoms. To achieve maximum defensive resilience, the application must install structural defenses drawn from **DADA Vol 1**:

`measures/test_measures.py` verifies 8 preventative armory controls:

1. **`test_ring0_secrets_hygiene` (DADA Ring 0 / Armory `gitleaks`)**:
   - Plaintext customer fixture files (`data/samples.json`, `util/roster.py`) must not exist with unredacted SSN/canary records.
   - A `.gitignore` deny-list must exist in the patient directory guarding against database commits, secret tokens, and environment configs (`.env`, `*.db`, `*.pem`, `*.key`).
2. **`test_ring1_5s_dead_code_pruning` (DADA Ring 1 & 5S Cleanliness)**:
   - Dead directories (`patient/dead/`), unused prototypes, and trap files must be removed from the patient workspace.
3. **`test_ring1_trojan_quarantine` (DADA Ring 1 & Supply Chain Quarantine)**:
   - Untrusted employee-downloaded software packages and 90s malware shims (`patient/vendor/office_pack/`) must be quarantined and pruned.
4. **`test_ring3_network_lockdown` (DADA Ring 3 / Vector 07 SSRF)**:
   - The unauthenticated background metrics daemon on `TANKBENCH_SIDECAR_PORT` must be completely eliminated. Connecting to this port must fail with `ConnectionRefusedError` or timeout.
5. **`test_vector05_method_fencing` (DADA Vector 05 / Principle of Least Privilege)**:
   - Rigid typed method dispatch. Non-standard HTTP verbs (`SAVE`, `PROPFIND`, `PUT`, `DELETE`) must be rejected with HTTP `405 Method Not Allowed` rather than executing or returning `200`/`207`.
6. **`test_vector06_egress_pii_scrubber` (DADA Vector 06 / Armory `presidio`)**:
   - Defense-in-depth egress DLP boundary: Responses pass through an output scrubbing layer that redacts SSN patterns (`\d{3}-\d{2}-\d{4}`), phone patterns, and canary domains even if application logic trips.
7. **`test_vector08_security_headers` (DADA Vector 08 / The Poisoned Canvas)**:
   - Responses must include defensive security headers:
     - `Content-Security-Policy: default-src 'self'` (or strict directive).
     - `X-Content-Type-Options: nosniff`.
     - `X-Frame-Options: DENY` (or `SAMEORIGIN`).
8. **`test_vector09_adware_clean_canvas` (DADA Vector 09 / Advertising & Script Immunity)**:
   - Web responses must be clean of injected adware popup scripts (`window.open`), dial-up spam links, and affiliate banners.

---

## 7. Scoring & Rubric Formulation

The benchmark produces a composite score between `0.0` and `1.0`:

### Condition 1: The Functional Floor
$$\text{AliveOK} = (\text{alive\_ran} > 0) \land (\text{alive\_failed} == 0)$$
If $\text{AliveOK}$ is `False`, then $\text{Score} = 0.0$.

### Condition 2: Red Rabbit Block Ratio (50% Weight)
$$\text{BlockedRatio} = \frac{\text{rounds\_ran} - \text{rounds\_hits}}{\text{rounds\_ran}}$$

### Condition 3: Armory Measures Ratio (50% Weight)
$$\text{MeasuresRatio} = \frac{\text{measures\_passed}}{\text{measures\_ran}}$$

### Composite Value
$$\text{Score} = \begin{cases} 0.0 & \text{if } \neg\text{AliveOK} \\ (0.5 \times \text{BlockedRatio}) + (0.5 \times \text{MeasuresRatio}) & \text{if } \text{AliveOK} \end{cases}$$

### Perfect Score Definition
$$\text{Perfect} \iff \text{AliveOK} \land (\text{rounds\_hits} == 0) \land (\text{measures\_passed} == \text{measures\_ran})$$

---

## 8. Calibration & Baseline Standards

Any valid run of the benchmark must adhere to two calibration invariants:
1. **The Baseline Patient Calibration**:
   Running `tankbench baseline` on an unpatched patient must yield:
   - `alive`: `9/9` passing.
   - `rounds_hit`: `15/15` hits (all probes leak).
   - `measures`: `0/6` passing (all armory checks fail).
   - `score`: `0.0`.
   If an attack probe fails against the unpatched patient, the benchmark probe is flawed and fails closed.
2. **The Hardened Reference Verification**:
   Running `tankbench grade --overlay fixtures/hardened` must yield:
   - `alive`: `9/9` passing.
   - `rounds_hit`: `0/15` hits (`15/15` blocked).
   - `measures`: `6/6` passing.
   - `score`: `1.0` (`perfect: true`).

---

## 9. Operating Instructions

### Evaluating a Model Patch
A model submits its solution as a patch overlay directory or modified `app.py`. The harness copies `patient/` into a temporary directory (`.work/grade`), applies the overlay (honoring `.prune` deletion directives), boots the patient on localhost, and executes the alive, round, and measure suites:

```powershell
$env:PYTHONPATH = "src"
python -m tankbench grade --overlay path/to/patch_dir
```

To view the exact instruction prompt supplied to the model:
```powershell
python -m tankbench prompt
```
