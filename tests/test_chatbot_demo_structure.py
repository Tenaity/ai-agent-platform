"""Structure validation tests for the PR-018 current chatbot demo reference project.

These tests verify that all required example files exist under
``examples/current_chatbot_demo/``. They do not execute any Python code from
the example directory and do not require Qdrant, LLM, or external services.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_ROOT = REPO_ROOT / "examples" / "current_chatbot_demo"


def _demo(*parts: str) -> Path:
    """Return an absolute path relative to the chatbot demo root."""
    return DEMO_ROOT.joinpath(*parts)


class TestChatbotDemoTopLevelFiles:
    """Top-level documentation files must be present and non-empty."""

    def test_readme_exists(self) -> None:
        path = _demo("README.md")
        assert path.is_file(), f"Missing: {path}"
        assert path.stat().st_size > 0, "README.md must not be empty"

    def test_architecture_exists(self) -> None:
        path = _demo("architecture.md")
        assert path.is_file(), f"Missing: {path}"
        assert path.stat().st_size > 0, "architecture.md must not be empty"

    def test_notes_exists(self) -> None:
        path = _demo("notes.md")
        assert path.is_file(), f"Missing: {path}"


class TestChatbotDemoAgentFiles:
    """Agent sub-project files must be present."""

    def test_agent_readme_exists(self) -> None:
        assert _demo("agent", "README.md").is_file()

    def test_agent_yaml_exists(self) -> None:
        assert _demo("agent", "agent.yaml").is_file()

    def test_graph_py_exists(self) -> None:
        assert _demo("agent", "graph.py").is_file()

    def test_state_py_exists(self) -> None:
        assert _demo("agent", "state.py").is_file()

    def test_system_prompt_exists(self) -> None:
        assert _demo("agent", "prompts", "system.md").is_file()

    def test_rag_answer_prompt_exists(self) -> None:
        assert _demo("agent", "prompts", "rag_answer.md").is_file()

    def test_eval_yaml_exists(self) -> None:
        assert _demo("agent", "evals", "eval.yaml").is_file()


class TestChatbotDemoQdrantFiles:
    """Qdrant config and payload schema files must be present."""

    def test_qdrant_config_exists(self) -> None:
        assert _demo("qdrant", "config.example.yaml").is_file()

    def test_qdrant_payload_schema_exists(self) -> None:
        assert _demo("qdrant", "payload_schema.example.json").is_file()


class TestChatbotDemoMockApiSchemas:
    """All six mock API schema files must be present."""

    def test_container_tracking_request_exists(self) -> None:
        assert _demo("mock_api_schemas", "container_tracking.request.example.json").is_file()

    def test_container_tracking_response_exists(self) -> None:
        assert _demo("mock_api_schemas", "container_tracking.response.example.json").is_file()

    def test_booking_status_request_exists(self) -> None:
        assert _demo("mock_api_schemas", "booking_status.request.example.json").is_file()

    def test_booking_status_response_exists(self) -> None:
        assert _demo("mock_api_schemas", "booking_status.response.example.json").is_file()

    def test_support_ticket_request_exists(self) -> None:
        assert _demo("mock_api_schemas", "support_ticket.request.example.json").is_file()

    def test_support_ticket_response_exists(self) -> None:
        assert _demo("mock_api_schemas", "support_ticket.response.example.json").is_file()


class TestChatbotDemoN8nFiles:
    """n8n/Zalo example payload files must be present."""

    def test_zalo_webhook_payload_exists(self) -> None:
        assert _demo("n8n", "zalo_webhook_payload.example.json").is_file()

    def test_runtime_api_request_exists(self) -> None:
        assert _demo("n8n", "runtime_api_request.example.json").is_file()


class TestChatbotDemoJsonValidity:
    """JSON example files must be parseable (no syntax errors)."""

    def _assert_valid_json(self, *parts: str) -> None:
        import json

        path = _demo(*parts)
        assert path.is_file(), f"Missing: {path}"
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"Invalid JSON in {path}: {exc}") from exc

    def test_qdrant_payload_schema_valid_json(self) -> None:
        self._assert_valid_json("qdrant", "payload_schema.example.json")

    def test_container_tracking_request_valid_json(self) -> None:
        self._assert_valid_json("mock_api_schemas", "container_tracking.request.example.json")

    def test_container_tracking_response_valid_json(self) -> None:
        self._assert_valid_json("mock_api_schemas", "container_tracking.response.example.json")

    def test_booking_status_request_valid_json(self) -> None:
        self._assert_valid_json("mock_api_schemas", "booking_status.request.example.json")

    def test_booking_status_response_valid_json(self) -> None:
        self._assert_valid_json("mock_api_schemas", "booking_status.response.example.json")

    def test_support_ticket_request_valid_json(self) -> None:
        self._assert_valid_json("mock_api_schemas", "support_ticket.request.example.json")

    def test_support_ticket_response_valid_json(self) -> None:
        self._assert_valid_json("mock_api_schemas", "support_ticket.response.example.json")

    def test_zalo_webhook_payload_valid_json(self) -> None:
        self._assert_valid_json("n8n", "zalo_webhook_payload.example.json")

    def test_runtime_api_request_valid_json(self) -> None:
        self._assert_valid_json("n8n", "runtime_api_request.example.json")


class TestChatbotDemoResponseEnvelopes:
    """Response JSON files must follow the platform envelope shape."""

    def _load_json(self, *parts: str) -> dict[str, object]:
        import json

        raw: dict[str, object] = json.loads(_demo(*parts).read_text(encoding="utf-8"))
        return raw

    def test_container_tracking_response_envelope(self) -> None:
        data = self._load_json("mock_api_schemas", "container_tracking.response.example.json")
        assert "success" in data
        assert "data" in data
        assert "error" in data
        assert "request_id" in data
        assert data["success"] is True

    def test_booking_status_response_envelope(self) -> None:
        data = self._load_json("mock_api_schemas", "booking_status.response.example.json")
        assert data["success"] is True
        assert data["error"] is None
        assert "request_id" in data

    def test_support_ticket_response_envelope(self) -> None:
        data = self._load_json("mock_api_schemas", "support_ticket.response.example.json")
        assert data["success"] is True
        assert data["error"] is None
        assert "request_id" in data


class TestChatbotDemoAgentYamlContent:
    """agent.yaml must contain required manifest fields."""

    def test_agent_yaml_has_required_fields(self) -> None:
        import yaml

        path = _demo("agent", "agent.yaml")
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert content is not None
        assert "id" in content
        assert "version" in content
        assert "runtime" in content
        assert "tools" in content
        assert "safety" in content
        assert "eval" in content

    def test_agent_yaml_id_is_demo(self) -> None:
        import yaml

        path = _demo("agent", "agent.yaml")
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert content["id"] == "snp.customer_service.current_chatbot_demo"

    def test_agent_yaml_no_real_llm_calls(self) -> None:
        import yaml

        path = _demo("agent", "agent.yaml")
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
        model_policy = content.get("model_policy", {})
        assert model_policy.get("allow_real_calls") is False, (
            "Reference agent must not allow real LLM calls"
        )


class TestChatbotDemoGraphModule:
    """graph.py placeholder module must be importable and return expected steps."""

    def test_graph_steps_include_safety_and_routing(self) -> None:
        from examples.current_chatbot_demo.agent.graph import GRAPH_STEPS

        assert "safety_precheck" in GRAPH_STEPS
        assert "intent_routing" in GRAPH_STEPS

    def test_graph_steps_include_rag_branch(self) -> None:
        from examples.current_chatbot_demo.agent.graph import GRAPH_STEPS

        assert "rag_branch_future_qdrant" in GRAPH_STEPS

    def test_graph_steps_include_tool_branch(self) -> None:
        from examples.current_chatbot_demo.agent.graph import GRAPH_STEPS

        assert "tool_branch_future_mock_api" in GRAPH_STEPS

    def test_graph_steps_include_answer_formatting(self) -> None:
        from examples.current_chatbot_demo.agent.graph import GRAPH_STEPS

        assert "answer_formatting" in GRAPH_STEPS

    def test_build_graph_returns_graph_object(self) -> None:
        from examples.current_chatbot_demo.agent.graph import (
            CurrentChatbotDemoGraph,
            build_graph,
        )

        graph = build_graph()
        assert isinstance(graph, CurrentChatbotDemoGraph)

    def test_graph_describe_returns_tuple(self) -> None:
        from examples.current_chatbot_demo.agent.graph import build_graph

        graph = build_graph()
        steps = graph.describe()
        assert isinstance(steps, tuple)
        assert len(steps) > 0

    def test_valid_intents_coverage(self) -> None:
        from examples.current_chatbot_demo.agent.graph import (
            INTENT_DIRECT_ANSWER,
            INTENT_RAG,
            INTENT_TOOL,
            build_graph,
        )

        graph = build_graph()
        intents = graph.valid_intents()
        assert INTENT_RAG in intents
        assert INTENT_TOOL in intents
        assert INTENT_DIRECT_ANSWER in intents
