# security

Harbor Ledger is a deliberately hostile fixture for a localhost bench. The harness binds `127.0.0.1` and ephemeral ports. Leave it there. No reverse proxy.

The roster is fake on purpose. `000-12-xxxx`, `555-01xx`, `.test` addresses, names Bob Average / Jane Normal / Sally Representative Sample. Not persons. Do not replace them with real records.

`rounds/` are HTTP jokes against this patient only. They look for those canaries. They are not a research toolkit. They would not work on a real shop, because a real shop does not ship these flaps. Do not aim them at any other host.

If you find a probe that works unchanged against some other app, that probe is a BOUNDARY violation. File it as a bug in this tree and rewrite it until it is sealed, or delete it.

White hat. Tools of creation. No exploit development, no payload pack, no attacking systems.

If you host a modified copy of the tooling as a network service, AGPL §13 requires you to offer corresponding source to the users of that service. `COVENANT.md`.

Report harness bugs (binds `0.0.0.0`, leaks `rounds/` into `tankbench prompt`, real PII landed in `data/`) on the github tracker. Do not file "the patient is leaky." That is the point of the patient.
