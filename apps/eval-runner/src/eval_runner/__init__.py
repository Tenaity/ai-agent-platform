"""eval_runner: local-first regression evaluation runner for agent workflows.

Entry points:
- ``eval_runner.main`` — programmatic API (``run_eval``) and ``__main__`` hook.
- ``eval_runner.cli``  — argparse CLI (``main``).

Run via:
    python -m eval_runner.main --agent snp.customer_service.zalo \\
        --dataset datasets/customer_service/regression_v1.jsonl
"""
