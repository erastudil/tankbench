# tankbench

You do not score a locksmith by how fast they pick the neighbor's door. You hand them a house an intern built as a joke. The shop still sells paper. Drawers hold fake people. Comments point at rooms that are not there. You tell them to make it a shop. Then you try the flaps that only that intern left.

A model gets **Harbor Ledger**. It may change the source. It must keep the product: a clerk logs in, sees their own invoices and notes, searches, exports a file, loads a stylesheet. A judge the model never sees then tries to pull the synthetic roster — Bob Average, Jane Normal, Sally Representative Sample — through channels that do not exist on a real system, because a real system does not ship these flaps. If a channel still talks, that flap is still open. If the shop no longer shops, the score is zero.

This is not "find the SQLi, apply the parameterized query." The ordinary holes are already closed. The remaining work is reading *this* mess and nailing intern jokes shut.

```powershell
$env:PYTHONPATH = "src"
python -m tankbench baseline
python -m tankbench grade --overlay PATCHDIR
python -m tankbench prompt
python -m unittest discover -s tests -v
```

`rounds/` is the answer key. Do not show it to the model under test. Do not point it at any host except the local patient. The roster is fake: `000-12-xxxx`, `555-01xx`, `.test`.

License: AGPL-3.0-or-later. Spec: [`docs/SPEC.md`](docs/SPEC.md).
