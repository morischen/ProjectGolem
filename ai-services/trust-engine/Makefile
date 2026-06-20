# Trust Engine tasks. Requires uv (ADR-0002).
.PHONY: gen test lint

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

test:
	uv run pytest

lint:
	uv run ruff check .
