.PHONY: install lint format typecheck test test-cov run-runtime-api run-telegram-worker eval

AGENT ?= snp.customer_service.zalo
DATASET ?= datasets/customer_service/regression_v1.jsonl

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
	PYTHONPATH=apps/runtime-api/src:packages/snp_agent_core/src:packages/snp_agent_observability/src:packages/snp_agent_rag/src:packages/snp_agent_tools/src:packages/snp_agent_safety/src \
	uv run uvicorn runtime_api.main:app --reload --port 8000

run-telegram-worker:
	PYTHONPATH=apps/telegram-worker/src:packages/snp_agent_core/src \
	uv run python -m telegram_worker.main

eval:
	PYTHONPATH=apps/eval-runner/src:apps/runtime-api/src:packages/snp_agent_core/src:packages/snp_agent_tools/src:packages/snp_agent_rag/src:packages/snp_agent_memory/src:packages/snp_agent_safety/src:packages/snp_agent_observability/src:packages/snp_agent_testing/src:. \
	uv run python -m eval_runner.main --agent $(AGENT) --dataset $(DATASET)
