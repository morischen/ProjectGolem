# Trust Engine

The deterministic scoring core of the Evidence Intelligence Platform. It is the
**only** component that produces confidence scores and verdicts, and it does so as
a pure function of classified evidence plus a versioned weights config. **LLMs
never score** (see [ADR-0003](../../docs/adr/0003-deterministic-trust-engine.md) /
INV-DETERMINISM).

## Model
Confidence is the blueprint §10 weighted sum of five components, each in `[0, 1]`:

```
0.30 source_reliability + 0.25 corroboration + 0.20 evidence_quality
+ 0.15 independence + 0.10 freshness
```

Direction and conflict come from support vs. contradiction *mass*
(`tier_reliability × quality`). Verdict mapping (order matters):

1. strength `< strength_floor` → **Insufficient Evidence**
2. minority-mass share `≥ mixed_conflict_threshold` → **Mixed Evidence** (never
   force a side — INV-FORCE)
3. otherwise directional: `≥ verified_threshold` → **Verified** / **False**,
   else **Likely True** / **Likely False**

`independence` (`1 − 1/distinct_sources`) and corroboration over *distinct* sources
mean evidence laundered through a single source cannot reach Verified.

## Develop & test
```bash
# from this directory — uv is the standard toolchain (ADR-0002)
uv sync            # creates .venv + installs deps from uv.lock (incl. dev group)
uv run pytest      # run the suite in the synced env

# fallback without uv:
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
`uv.lock` is committed for reproducible installs (INV-REPRO).

## Status
First vertical. Models are hand-authored here for now; per ARCHITECTURE.md §3 they
will move to code-generation from `contracts/` once that toolchain is chosen.
