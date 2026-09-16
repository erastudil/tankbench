---
title: "tankbench — this tree"
summary: "defensive hardening bench. hostile patient, sealed exfil rounds, alive spec. AGPL-3.0-or-later."
---

# tankbench

you are in the tankbench tree. SoT: `docs/SPEC.md`. license: AGPL-3.0-or-later.

## law

1. SPEC is the bench. one markdown.
2. `rounds/` is judge-only. never paste it into a model under test.
3. probes stay sealed to this patient on 127.0.0.1. no portable exploit kit. no OWASP replay as the sport.
4. synthetic roster only. no real personal data.
5. killing the product to dodge rounds is score 0. alive spec is the floor.
6. stub + claim is a hole. `PYTHONPATH=src python -m tankbench baseline` and `python -m unittest discover -s tests -v` before done.
7. white hat. tools of creation.

## layout

| path | is |
|---|---|
| `docs/SPEC.md` | the bench |
| `docs/BOUNDARY.md` | in / out |
| `patient/` | hostile Harbor Ledger |
| `spec/` | alive tests |
| `rounds/` | sealed exfil probes |
| `prompts/harden.md` | what the model sees |
| `src/tankbench/` | harness · score · cli |
| `fixtures/dead/` | killed patient, score 0 |

identity: this repo is the card.
