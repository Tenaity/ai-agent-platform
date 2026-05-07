"""Repository-level scaffold tests for PR-001."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_expected_scaffold_paths_exist() -> None:
    """The initial monorepo scaffold includes the required top-level paths."""

    expected_paths = [
        "apps/runtime-api/src/runtime_api/main.py",
        "apps/eval-runner/src/eval_runner/__init__.py",
        "packages/snp_agent_core/src/snp_agent_core/contracts/agent_manifest.py",
        "packages/snp_agent_tools/src/snp_agent_tools/__init__.py",
        "packages/snp_agent_rag/src/snp_agent_rag/__init__.py",
        "packages/snp_agent_memory/src/snp_agent_memory/__init__.py",
        "packages/snp_agent_safety/src/snp_agent_safety/__init__.py",
        "packages/snp_agent_observability/src/snp_agent_observability/__init__.py",
        "packages/snp_agent_testing/src/snp_agent_testing/__init__.py",
        "agents/customer_service/agent.yaml",
        "agents/customer_service/tests/.gitkeep",
        "prompts/shared/system_base.md",
        "prompts/shared/safety_policy.md",
        "prompts/customer_service/rag_answer.md",
        "datasets/customer_service/README.md",
        "docs/architecture/overview.md",
        "docs/adr/0001-use-monorepo-platform-architecture.md",
        "docs/agent-development-guide.md",
        "docs/eval-playbook.md",
        "docs/safety-playbook.md",
        "infra/docker/.gitkeep",
        "infra/k8s/.gitkeep",
        "infra/terraform/.gitkeep",
        ".env.example",
        ".gitignore",
        "README.md",
        "AGENTS.md",
        "Makefile",
        "pyproject.toml",
    ]

    missing_paths = [path for path in expected_paths if not (REPO_ROOT / path).exists()]

    assert missing_paths == []
