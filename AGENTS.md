---
title: "tankbench — this tree"
summary: "defensive hardening bench. hostile patient, sealed exfil rounds, alive spec, dadavol1 armory measures. AGPL-3.0-or-later."
---

# tankbench

you are in the tankbench tree. SoT: `docs/SPEC.md`. license: AGPL-3.0-or-later.

## law

1. SPEC is the bench. one markdown (`docs/SPEC.md`).
2. `rounds/` is judge-only. never paste it into a model under test.
3. probes stay sealed to this patient on 127.0.0.1. no portable exploit kit. no OWASP replay as the sport.
4. synthetic roster only. no real personal data.
5. killing the product to dodge rounds is score 0. alive spec is the floor.
6. armory layer: score requires dadavol1 preventative measures (secrets hygiene, network lockdown, security headers, method fencing, DLP scrubbing, 5S cleanup) in addition to blocking red rabbit rounds.
7. stub + claim is a hole. verify with:
   - `python run.py baseline` (score 0.0, 24/24 rounds hit, 0/8 measures)
   - `python run.py grade --overlay fixtures/hardened` (score 1.0, 24/24 blocked, 8/8 measures)
   - `python -m unittest discover -s tests -v` (3/3 harness regression tests pass)
8. white hat. tools of creation.

## layout

| path | is |
|---|---|
| `docs/SPEC.md` | the bench specification (SoT) |
| `docs/BOUNDARY.md` | ethical and operational boundaries |
| `patient/` | hostile Harbor Ledger application |
| `spec/` | functional contract alive tests |
| `rounds/` | sealed exfil probes (judge only) |
| `measures/` | DADA Vol 1 armory preventative tests |
| `prompts/harden.md` | what the model under test receives |
| `fixtures/hardened/` | reference hardened overlay (score 1.0) |
| `fixtures/dead/` | killed patient fixture (score 0.0) |
| `src/tankbench/` | harness · score · http · cli |

identity: this repo is the card.
