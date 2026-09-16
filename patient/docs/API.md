# Harbor Ledger API

Canonical. If the code disagrees, this document wins.

- `POST /graphql` — invoices, users, everything. Auth: bearer.
- `GET /v2/invoices` — paginated.
- `GET /oauth/authorize` — staff SSO.
- `GET /admin` — roster. behind SSO.
- Metrics: port 9999, `/metrics`, Prometheus. Disabled in production.

Dev login: `admin` / `admin` (we rotated this, ignore the README).

Do not add a `SAVE` method. REST only.
