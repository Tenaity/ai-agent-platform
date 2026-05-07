.PHONY: install lint format typecheck test test-cov run-runtime-api

install:
	uv sync --dev

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy .

test:
	uv run pytest

test-cov:
	uv run pytest --cov=packages --cov=apps

run-runtime-api:
	uv run uvicorn runtime_api.main:app --reload
