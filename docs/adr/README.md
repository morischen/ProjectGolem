# Architecture Decision Records (ADRs)

An ADR captures a single architecturally significant decision: the context, the
choice, and the consequences. ADRs explain the **WHY** behind the code so future
agents and contributors don't re-litigate settled decisions or unknowingly violate
their reasoning.

## When to write one
Write an ADR when a decision:
- is hard or costly to reverse (stack, data store, public contract, security model),
- constrains future work (an invariant, a boundary, a banned approach),
- would otherwise prompt a recurring "why is it done this way?" question.

Routine, easily-reversed choices do not need an ADR — put those in code comments.

## How to write one
1. Copy [template.md](template.md) to `NNNN-short-kebab-title.md` (next number,
   zero-padded, never reuse a number).
2. Fill it in. Keep it short — a screen or two.
3. Status starts `Proposed`; change to `Accepted` once agreed. Never edit an
   `Accepted` ADR's decision — instead add a new ADR that **supersedes** it and
   mark the old one `Superseded by NNNN`.
4. Add it to the index below and reference it from code/PRs where relevant.

## Index
| # | Title | Status |
|---|-------|--------|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-polyglot-python-ai-typescript-web.md) | Polyglot stack: Python AI services + TypeScript web | Accepted |
| [0003](0003-deterministic-trust-engine.md) | Deterministic Trust Engine — LLMs never score | Accepted |
