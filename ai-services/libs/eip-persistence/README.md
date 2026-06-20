# eip-persistence

Bitemporal, append-only verdict persistence ([ADR-0008](../../../docs/adr/0008-bitemporal-verdict-store.md)).
Verdicts accrue immutable, versioned `VerdictRecord`s; nothing is mutated in place
(INV-TEMPORAL). Two time axes — **knowledge time** (when assessed) and **event
time** (when it happened) — and `as_of(t)` answers "what did we conclude on date X".
Timestamps are caller-supplied, so the store is deterministic (INV-REPRO).

## Implementations (one `VerdictStore` protocol)
- `InMemoryVerdictStore` — hermetic default for tests.
- `SqlVerdictStore` — SQLAlchemy Core; same code on SQLite (tests) and Postgres.

## Develop & test
```bash
uv sync
make qa     # lint + typecheck + test  (SQL tests run on in-memory SQLite — no DB)
```

## Run on Postgres (infra/docker-compose)
```bash
docker compose -f infra/docker-compose.yml up -d postgres
pip install "psycopg[binary]"   # Postgres driver (not a default dep; SQLite needs none)
```
```python
from eip_persistence import make_postgres_store
store = make_postgres_store("postgresql+psycopg://eip:devpassword@localhost:5432/eip")
```

## Status
Q1 (bitemporal core) + Q2 (SQL adapter) done. Next: an audit log and wiring the
store into the pipeline so each verdict is persisted.
