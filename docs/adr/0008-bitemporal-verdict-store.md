# 0008. Bitemporal verdict persistence

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Project lead
- **Related:** CLAUDE.md §3 (INV-TEMPORAL, INV-TRACE); base blueprint Principle 5 ("new evidence can overturn conclusions"); ARCHITECTURE.md §2, §7

## Context
Verdicts change as evidence arrives, and the platform must always answer "what did
we conclude on date X, and why did it change?" (INV-TEMPORAL). That requires
append-only, versioned verdict records with two time axes — **knowledge time** (when
the assessment was made) and **event time** (when the underlying event occurred) —
never in-place mutation. We also want this testable without a live database.

## Decision
A `VerdictStore` protocol over **immutable, append-only `VerdictRecord`s**, each
carrying `claim_id`, a monotonic per-claim `version`, the verdict/score/weights
version, `knowledge_time`, optional `event_time`, and the full result `payload`.
Operations: `append`, `latest`, `history`, and `as_of(knowledge_time)` (the version
that was current at a past instant). **Timestamps are supplied by the caller**, never
read from the clock inside the store — keeping it pure, deterministic, and
reproducible (INV-REPRO). `InMemoryVerdictStore` is the hermetic default for
tests/CI; a Postgres adapter (Q2) implements the same protocol for production.

## Consequences
- Conclusions are never overwritten — they accrue versions; the audit/correction
  story (public corrections, calibration ledger) builds directly on this.
- "As-of" queries make historical reproducibility a first-class operation.
- Lives in a shared lib (`eip-persistence`) so any service can persist verdicts
  behind one protocol.
- The store records what it's given; correctness of `event_time`/`payload` is the
  caller's responsibility.

## Alternatives considered
- **Mutable "current verdict" row** — violates INV-TEMPORAL; loses history. Rejected.
- **Single time axis (knowledge time only)** — can't order by when events occurred;
  event_time is cheap to carry now and hard to backfill later. Kept both.
