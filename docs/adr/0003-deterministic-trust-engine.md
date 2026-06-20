# 0003. Deterministic Trust Engine — LLMs never score

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Project lead
- **Related:** [CLAUDE.md](../../CLAUDE.md) §3 (INV-DETERMINISM); [ARCHITECTURE.md](../../ARCHITECTURE.md) §4.5; base blueprint §10, §16

## Context
The platform's credibility depends on verdicts being explainable, auditable, and
reproducible. LLM outputs are non-deterministic and not directly auditable as a
scoring mechanism: the same prompt can yield different numbers, and the "reasoning"
behind a generated score cannot be inspected or recomputed. If confidence scores or
verdicts came from an LLM, no two runs could be guaranteed equal and no score could
be defended on methodology grounds.

## Decision
We will compute **all** confidence scores, source weights, and final verdicts in a
**deterministic Trust Engine** — pure functions, no LLM or network calls in the
scoring path, weights in versioned config. LLMs are restricted to language tasks:
extraction, classification (with rationale), summarization, and explanation. An LLM
**never** produces a confidence number or a verdict.

We further acknowledge that LLM-driven evidence *classification* is an upstream
scoring input; it therefore carries per-item rationale, a human-override path
(INV-OVERRIDE), and full reproducibility metadata (model ID + prompt + inputs).

## Consequences
- Verdicts are reproducible and defensible; the same inputs + config version always
  yield the same score (unit-testable with fixed fixtures).
- The architectural boundary between the Reasoning Engine (explains) and the Trust
  Engine (scores) must be enforced in code and review — explanations may never feed
  scores, and scores may never originate in an LLM.
- Weight/methodology changes are versioned events; old verdicts remain reproducible
  against the config version that produced them.
- Some nuance that an LLM might "intuit" must instead be expressed as explicit,
  inspectable scoring features — more upfront design work, by design.

## Alternatives considered
- **LLM-generated confidence with prompt-logging** — not reproducible or auditable
  as a score; defeats the platform's core promise. Rejected.
- **Hybrid: LLM proposes score, deterministic system adjusts** — still injects
  non-determinism into the number; the score's provenance becomes unprovable. Rejected.
