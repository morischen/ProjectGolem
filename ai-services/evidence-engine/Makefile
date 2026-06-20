# Evidence Retrieval Engine tasks. Requires uv (ADR-0002).
.PHONY: gen lint typecheck test smoke qa

# Regenerate the Evidence Pydantic model from ../../contracts (ADR-0004).
gen:
	mkdir -p src/eip_evidence/_generated
	uv run datamodel-codegen \
		--input-file-type jsonschema \
		--output-model-type pydantic_v2.BaseModel \
		--capitalise-enum-members --use-annotated --use-double-quotes \
		--disable-timestamp --formatters black isort \
		--input ../../contracts/evidence.schema.json \
		--output src/eip_evidence/_generated/evidence.py

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

test:
	uv run pytest

smoke:
	uv run python scripts/smoke.py

qa: lint typecheck test smoke
