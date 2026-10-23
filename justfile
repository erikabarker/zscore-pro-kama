sync:
    uv sync --locked

test:
    uv run pytest -q

lint:
    uv run ruff check .
    uv run ruff format --check .

typecheck:
    uv run mypy

demo:
    uv run python examples/research_demo.py

audit:
    uv run python examples/audit_archived_results.py

build:
    uv build

check: test lint typecheck demo audit build
