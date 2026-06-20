# End-to-end integration tests. Requires uv (ADR-0002).
.PHONY: lint test qa

lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest

qa: lint test
