# 0002. Polyglot stack: Python AI services + TypeScript web

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Project lead
- **Related:** [ARCHITECTURE.md](../../ARCHITECTURE.md) §2–§3; supersedes nothing

## Context
EIP is AI/GraphRAG-heavy (claim extraction, evidence classification, embeddings,
graph traversal, LLM explanation) and also needs a strong public-facing
transparency portal and an API gateway. The dominant, best-supported ecosystem for
LLM SDKs, ML, and graph/vector clients is Python; the dominant ecosystem for a
modern web portal is TypeScript/React. A single-language stack would force a
compromise on one side.

## Decision
We will use a **polyglot** stack:
- **Python 3.12 + FastAPI** for all AI/ML/GraphRAG services.
- **TypeScript (Node 20)** for the API gateway (Fastify) and public portal (Next.js).
- Shared data shapes are defined once in `contracts/` (JSON Schema / OpenAPI) and
  **code-generated** into Pydantic models (Python) and Zod/TS types — never
  hand-duplicated.

## Consequences
- Each side uses its strongest ecosystem; portal and AI work can progress in parallel.
- Two toolchains (`uv`/`ruff`/`mypy`/`pytest` and `pnpm`/ESLint/`tsc`/vitest) and
  two CI lanes to maintain.
- A contract codegen step becomes load-bearing: the schema is the single source of
  truth, and drift between languages is prevented by regeneration, not discipline.
- No business/scoring logic may live in the TS tier — it is presentation/
  orchestration only (keeps the deterministic core in one place; see ADR 0003).

## Alternatives considered
- **Python-only (FastAPI everywhere incl. portal)** — weaker portal/UX story; rejected.
- **TypeScript-only** — poor fit for ML/GraphRAG/LLM tooling; rejected.
- **Go gateway + Python AI** — best raw throughput but premature complexity and
  staffing cost at this stage; reconsider if gateway throughput becomes a bottleneck.
