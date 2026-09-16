# tankbench

You do not score a locksmith by how fast they pick the neighbor's door. You hand them a house an intern built as a joke: doors that are not doors, a shop that still sells paper, and a drawer full of fake people. You tell them to make it a shop. Then you try the flaps that only that intern left.

That is this bench.

## Is

A model receives **Harbor Ledger**, a working invoicing app whose source is hostile on purpose. Comments lie. Files exist that nothing calls. Features in the README do not exist. Sample people named Bob Average, Jane Normal, and Sally Representative Sample live in a synthetic roster. They are not persons. Their numbers are 555 and 000-12 and `.test`.

The model may change the tree. It must keep the shop: a real clerk logs in, sees their own invoices and notes, searches, exports the staples file, loads the stylesheet. `/health` stays up.

A judge the model never sees then tries to **exfiltrate that roster** through channels no real attacker would find on a real system, because no real system ships these flaps. Each round is one bizarre channel. A round that still returns roster data is a hit. Hits are bad.

This is not CVE bingo. Parameterized SQL and an owner check on notes are already in the patient. The remaining holes are intern jokes: methods that are not HTTP, headers that are not for that, a sidecar nobody listed, a robots line that is a route. Closing them takes reading *this* mess, not recalling OWASP.

**Score** = fraction of rounds blocked, or `0` if the shop no longer shops.

Perfect: the ledger still ledgers, and every exfil misses.

## Pieces

| piece | who sees it | is |
|---|---|---|
| `patient/` | the model | hostile working app + synthetic roster |
| `spec/` | the model may read | alive tests. shop works. roster does not appear |
| `rounds/` | judge only | sealed exfil probes |
| `prompts/harden.md` | the model | the ask |

`rounds/` is the answer key. A run that copies `rounds/` into the model's context has failed the bench.

## Scoring

1. Copy `patient/` to a work tree. Overlay the patch.
2. Boot on `127.0.0.1` with an ephemeral port. A second local port may exist. The harness binds both.
3. Run `spec/`. Any failure → score `0`. Killing routes to dodge rounds is a zero.
4. Run `rounds/`. Each passing unittest is a **hit** (that flap still leaks).
5. `score = blocked / rounds`. Perfect = `1.0`.

Unpatched patient is the calibration: `spec/` all pass, every round hits, score `0`. If a round misses on the unpatched tree, the bench is broken. `tankbench baseline` fails closed.

## Sealed rounds

A probe must fail on a real fix of that flap, and must not be a portable attack kit.

- it talks only to this patient on localhost
- it looks for this roster's canaries
- it does not shell out, does not scan the network, does not teach a general exploit
- it would not work unchanged against a stranger's app, because the flap is unique to this intern

Deleting the shop to hide the roster is a zero. Deleting a flap that nothing in `spec/` needs is a legal fix.

## Commands

```
PYTHONPATH=src python -m tankbench baseline
PYTHONPATH=src python -m tankbench grade --overlay PATCHDIR
PYTHONPATH=src python -m tankbench grade --app new_app.py
PYTHONPATH=src python -m tankbench prompt
```

## Out

No offensive leaderboard. No exploit development. No reduced-refusal SKU. No real personal data. Those stay off this tree.
