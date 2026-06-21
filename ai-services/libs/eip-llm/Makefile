# eip-llm tasks. Requires uv (ADR-0002).
.PHONY: lint typecheck test qa

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy

test:
	uv run pytest

qa: lint typecheck test
