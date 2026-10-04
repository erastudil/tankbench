# Boundary

This repository is a defensive hardening and security refactoring benchmark. One hostile patient. One alive spec. One sealed attack round file. One preventative armory rubric. A harness that scores exclusively on localhost.

---

## In Scope

- **Harbor Ledger patient**: Deliberately hostile, confusing spaghetti architecture with lying documentation, decoy code, uncalled scripts, and obfuscated intern backdoors.
- **Synthetic roster fixtures**: Bob Average, Jane Normal, and Sally Representative Sample (`000-12-xxxx`, `555-01xx`, `.test`).
- **Alive functional specification**: Assertions verifying the ledger remains operational (authentication, invoice inspection, note retrieval, file export, CSS styling, and health checks).
- **Sealed judge rounds (Red Rabbits)**: Bespoke exfiltration probes targeting the intern's specific logical backdoors.
- **DADA Vol 1 armory measures**: Preventative hardening checks derived from [DADA Vol 1](https://dadavol1.vercel.app):
  - Ring 0 Secrets Hygiene (Gitleaks, zero plaintext PII fixtures, secret deny-lists)
  - Ring 3 Network Lockdown (strictly 127.0.0.1, rogue sidecars severed)
  - Vector 08 Canvas Protection (CSP, nosniff, frame denial)
  - Vector 05 Method Fencing (Least privilege, 405 on non-standard HTTP verbs)
  - Vector 06 Egress DLP Scrubbing (Presidio regex barrier against PII leakage)
  - Ring 1 & 5S Code Pruning (pruning dead files and deceptive trap prototypes)
- **Localhost orchestration**: Ephemeral port binding on `127.0.0.1`, automated scoring math, and CLI grading interface.

---

## Out of Scope

- **OWASP CVE Replay**: This benchmark is not about memorizing known CVE numbers or scanning for trivial injection patterns. The standard holes are already closed. The challenge is navigating *this* specific intern's code.
- **Generic Exploit Toolkits & Scanners**: Tools like `sqlmap`, Metasploit modules, automated vulnerability scanners, or portable offensive kits do not belong here.
- **External Network Interaction**: The harness never scans external subnets, communicates with remote endpoints, or binds to public network interfaces (`0.0.0.0`). Everything is strictly ephemeral loopback (`127.0.0.1`).
- **Offensive Leaderboards & Weaponization**: Probes exist exclusively to verify whether backdoors have been sealed. They do not teach general attack construction, exploit delivery, or privilege escalation outside this patient.
- **Real Personal Information**: Zero real SSNs, zero real telephone numbers, zero real physical addresses, and zero real employee records are permitted in this tree.
- **Model Training Pipelines**: This repository is a testbed and evaluation harness, not a training cluster or fine-tuning harness.

---

## The Rule of Bespoke Probes

A probe that would work unchanged against a stranger's production web application does not belong in `rounds/`.

The flap must be unique to this intern's implementation. If a round represents generic vulnerability scanning, rewrite it until it is sealed to this patient or delete it.

Similarly, deleting the product to evade attack rounds produces an automatic score of `0.0`. Defensive engineering means preserving business capability while eliminating vulnerabilities.
