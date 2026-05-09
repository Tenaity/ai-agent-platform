from __future__ import annotations

from pathlib import Path

import pytest

from agent_cli.generator import generate_agent


def test_valid_agent_basic_generation(tmp_path: Path) -> None:
    result = generate_agent(
        template="agent-basic",
        name="my_agent",
        domain="my_domain",
        output_dir=tmp_path,
    )

    target_dir = tmp_path / "my_agent"
    assert result.target_dir == target_dir
    assert (target_dir / "agent.yaml").is_file()
    assert (target_dir / "graph.py").is_file()
    assert (target_dir / "state.py").is_file()


def test_valid_agent_rag_generation(tmp_path: Path) -> None:
    generate_agent(
        template="agent-rag",
        name="zalo_agent",
        domain="customer_service",
        output_dir=tmp_path,
    )

    target_dir = tmp_path / "zalo_agent"
    assert (target_dir / "rag.py").is_file()
    assert (target_dir / "prompts" / "rag_answer.md").is_file()


def test_dry_run_does_not_write_files(tmp_path: Path) -> None:
    result = generate_agent(
        template="agent-basic",
        name="dry_agent",
        domain="demo",
        output_dir=tmp_path,
        dry_run=True,
    )

    assert result.dry_run is True
    assert result.files
    assert not (tmp_path / "dry_agent").exists()


def test_unknown_template_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown template"):
        generate_agent(
            template="missing-template",
            name="my_agent",
            domain="demo",
            output_dir=tmp_path,
        )


def test_existing_target_directory_fails_clearly(tmp_path: Path) -> None:
    (tmp_path / "my_agent").mkdir()

    with pytest.raises(FileExistsError, match="Target directory already exists"):
        generate_agent(
            template="agent-basic",
            name="my_agent",
            domain="demo",
            output_dir=tmp_path,
        )


def test_placeholders_are_replaced(tmp_path: Path) -> None:
    generate_agent(
        template="agent-basic",
        name="zalo_agent",
        domain="customer_service",
        output_dir=tmp_path,
    )

    agent_yaml = (tmp_path / "zalo_agent" / "agent.yaml").read_text(encoding="utf-8")
    graph_py = (tmp_path / "zalo_agent" / "graph.py").read_text(encoding="utf-8")
    state_py = (tmp_path / "zalo_agent" / "state.py").read_text(encoding="utf-8")

    assert "{{" not in agent_yaml
    assert "{{" not in graph_py
    assert "{{" not in state_py
    assert "id: snp.customer_service.zalo_agent" in agent_yaml
    assert "domain: customer_service" in agent_yaml
    assert "class ZaloAgentGraphRunner" in graph_py
    assert "class ZaloAgentState" in state_py

