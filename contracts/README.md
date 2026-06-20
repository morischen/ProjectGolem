# contracts/

**Source of truth** for cross-service data shapes. These JSON Schemas
(draft 2020-12) are authored here and **code-generated** into language-specific
types — never hand-duplicated (CLAUDE.md §4 contracts rule, ADR-0002).

| Schema | Shape | Status |
|--------|-------|--------|
| [evidence.schema.json](evidence.schema.json) | `Evidence` + `EvidenceRelation` | consumed by trust-engine |
| [verdict.schema.json](verdict.schema.json) | `TrustResult` + `Verdict` + `ConfidenceBreakdown` | consumed by trust-engine |
| [claim.schema.json](claim.schema.json) | `Claim` + `ClaimType` | forward contract (Claim Engine, later) |

## Code generation

Toolchain decision: [ADR-0004](../docs/adr/0004-contract-codegen-toolchain.md).

**Python (Pydantic v2)** — generated into `ai-services/trust-engine/src/eip_trust/_generated.py`
(do not edit the generated file; edit the schema and regenerate):

```bash
cd ai-services/trust-engine
make gen        # wraps datamodel-codegen over ../../contracts
uv run pytest   # conformance tests validate model output against these schemas
```

**TypeScript** — deferred until the `web/` workspace exists; planned via
`json-schema-to-typescript` (see ADR-0004).

## Conventions
- `additionalProperties: false` on all objects (contracts are closed).
- Shared enums live in each schema's `$defs` (no cross-file `$ref` in v0).
- A schema change is a contract change: bump consumers and regenerate in the same loop.
