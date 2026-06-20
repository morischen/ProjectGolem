# Trust Engine tasks. Requires uv (ADR-0002).
.PHONY: gen lint typecheck test smoke bench serve qa

# Regenerate Pydantic contract models from ../../contracts (ADR-0004).
# Do not hand-edit src/eip_trust/_generated/ — edit the schema and run `make gen`.
gen:
	mkdir -p src/eip_trust/_generated
	for s in evidence verdict claim; do \
		uv run datamodel-codegen \
			--input-file-type jsonschema \
			--output-model-type pydantic_v2.BaseModel \
			--capitalise-enum-members --use-annotated --use-double-quotes \
			--disable-timestamp --formatters black isort \
			--input ../../contracts/$$s.schema.json \
			--output src/eip_trust/_generated/$$s.py; \
	done

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

test:
	uv run pytest

smoke:
	uv run python scripts/smoke.py

# Run the seed gold-benchmark (golden fixtures); fails if accuracy < 100%.
bench:
	uv run python scripts/run_benchmark.py

# Run the HTTP service locally.
serve:
	uv run uvicorn eip_trust.api:app --reload

# Full per-service gate: lint + types + tests + runtime smoke + benchmark.
qa: lint typecheck test smoke bench
