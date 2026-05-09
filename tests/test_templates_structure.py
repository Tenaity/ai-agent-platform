"""Structure checks for project templates and examples."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_required_template_and_example_files_exist() -> None:
    """Required scaffold and reference example files are present."""

    required_paths = [
        "templates/agent-basic/agent.yaml.template",
        "templates/agent-rag/rag.py.template",
        "templates/agent-tool/tools.py.template",
        "templates/agent-full-demo/safety.py.template",
        "examples/current_chatbot_demo/README.md",
        "examples/current_chatbot_demo/agent/agent.yaml",
        "examples/current_chatbot_demo/qdrant/config.example.yaml",
        "examples/current_chatbot_demo/qdrant/payload_schema.example.json",
        "examples/current_chatbot_demo/mock_api_schemas/container_tracking.response.example.json",
        "examples/current_chatbot_demo/n8n/runtime_api_request.example.json",
    ]

    missing = [path for path in required_paths if not (REPO_ROOT / path).is_file()]

    assert missing == []
