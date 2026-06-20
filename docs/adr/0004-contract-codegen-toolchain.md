# 0004. Contract codegen toolchain

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Project lead
- **Related:** [ADR-0002](0002-polyglot-python-ai-typescript-web.md); [ARCHITECTURE.md](../../ARCHITECTURE.md) §3, §8; [contracts/](../../contracts/)

## Context
ADR-0002 chose a polyglot stack with a single source of truth for cross-service
data shapes in `contracts/` (JSON Schema), code-generated into Pydantic models
(Python) and Zod/TS types (TypeScript) so the two languages never drift. That ADR
left the *generator* selection open (ARCHITECTURE.md §8). We now need it to migrate
the Trust Engine's hand-authored models onto the contracts.

## Decision
- **Python:** generate Pydantic v2 models with **`datamodel-code-generator`**
  (`datamodel-codegen`), run via `uv` as a dev dependency. Output is a single
  committed module, `src/eip_trust/_generated.py`, marked do-not-edit. Generation
  uses `--disable-timestamp` so output is deterministic (reproducible diffs,
  INV-REPRO). A `make gen` target wraps the command.
- **TypeScript:** **deferred** until the `web/` workspace exists. Planned generator
  is `json-schema-to-typescript` (or `quicktype`), to be confirmed in the loop that
  scaffolds `web/`. JSON Schema is the shared input either way.
- **Conformance over trust:** the engine's own behaviour-bearing config
  (`ScoringWeights`, thresholds) stays hand-authored — it is internal, not a
  cross-service contract. Generated models cover only the published shapes. A test
  suite validates that model instances serialize to data conforming to the schemas
  (via `jsonschema`), so drift fails CI regardless of generator quirks.

## Consequences
- One command regenerates Python types from the schemas; the schema is the only
  place a shared shape is defined.
- The generated module is committed (no generate-on-build step), keeping the test
  loop hermetic and diffs reviewable.
- TS consumers are unblocked the moment `web/` lands — no schema rework needed.
- Generator enum/field naming is pinned via flags (`--capitalise-enum-members`);
  if a future schema breaks the mapping, the conformance tests catch it.

## Alternatives considered
- **OpenAPI-first (generate schemas from code)** — inverts the source of truth;
  rejected, contracts must lead.
- **Hand-write Pydantic + TS and rely on review** — the exact drift ADR-0002 forbids.
- **Protobuf/Avro** — heavier, binary-oriented; JSON Schema fits our JSON APIs and
  document-shaped data better for now.
