# 0001. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-06-19
- **Deciders:** Project lead
- **Related:** [CLAUDE.md](../../CLAUDE.md) §1 (pre-session checklist)

## Context
This is a long-lived, AI-assisted project. Agents work in short loops with limited
context windows and rotate across sessions. Without a durable record of *why*
decisions were made, each session risks re-litigating settled choices or
unknowingly violating their rationale. Code records the WHAT; commit messages
record the immediate change; neither reliably preserves the WHY behind
architecturally significant choices.

## Decision
We will record architecturally significant decisions as ADRs in `docs/adr/`, one
markdown file per decision, using [template.md](template.md). The pre-session
checklist (CLAUDE.md §1) directs agents to read relevant ADRs before changing an
area. Accepted ADRs are immutable; a changed decision is captured as a new ADR that
supersedes the old one.

## Consequences
- New agents can recover intent quickly, reducing rework and accidental regressions.
- A small, ongoing documentation cost per significant decision.
- The ADR index in `README.md` must be kept current (enforced by review, not tooling).

## Alternatives considered
- **Decisions only in commit messages / PRs** — not discoverable later; intent gets buried.
- **A single design doc** — drifts, becomes monolithic, loses the per-decision audit trail.
