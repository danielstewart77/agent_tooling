# tests/test_tool_registry.py
import json
import sys
import importlib
from unittest.mock import patch
import pytest

from agent_tooling import tool, get_tool_schemas, get_tool_function, discover_tools
from agent_tooling.openai_client import OpenAITooling
from agent_tooling.tool import tool_registry

@pytest.fixture(autouse=True)
def clear_registry():
    # reset between tests
    tool_registry.tool_schemas.clear()
    tool_registry.tool_functions.clear()
    yield
    tool_registry.tool_schemas.clear()
    tool_registry.tool_functions.clear()

def test_direct_decorator_registration():
    @tool(tags=["test"])
    def double(x: int) -> int:
        """Double it."""
        return x * 2

    schemas = get_tool_schemas()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "double"
    fn = get_tool_function("double")
    assert fn is not None
    assert fn(3) == 6

def test_dynamic_discovery(tmp_path, monkeypatch):
    # 1) create a fake package
    pkg = tmp_path / "pkg_agents"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "mymod.py").write_text(
        "from agent_tooling import tool\n"
        "@tool\ndef greet(name: str) -> str:\n"
        "    return 'Hello ' + name\n"
    )

    # 2) patch sys.path
    monkeypatch.syspath_prepend(str(tmp_path))

    # 🛠 3) RE-IMPORT agent_tooling fresh under pytest sys.path
    import importlib
    import sys
    if "agent_tooling" in sys.modules:
        del sys.modules["agent_tooling"]
    agent_tooling = importlib.import_module("agent_tooling")

    # 4) force import the dynamic package
    importlib.import_module("pkg_agents")

    # 5) discover tools
    agent_tooling.discover_tools(["pkg_agents"])
    schemas = agent_tooling.get_tool_schemas()
    assert any(s["name"] == "greet" for s in schemas)

def test_openai_client_importable():
    # just ensure module loads under whichever name you choose
    # e.g. openai_client or openai
    import importlib
    try:
        m = importlib.import_module("agent_tooling.openai_client")
    except ModuleNotFoundError:
        m = importlib.import_module("agent_tooling.openai")
    assert hasattr(m, "OpenAITooling")

@pytest.fixture(autouse=True)
def clear_tool_registry():
    """Clear tool registry between tests."""
    tool_registry.clear()
    yield
    tool_registry.clear()

# Register three fake tools
@tool(tags=["alpha"])
def alpha_tool(question: str, messages: list[dict]) -> str:
    return "alpha response"

@tool(tags=["beta"])
def beta_tool(question: str, messages: list[dict]) -> str:
    return "beta response"

@tool(tags=["gamma"])
def gamma_tool(question: str, messages: list[dict]) -> str:
    return "gamma response"

@patch("agent_tooling.openai_client.OpenAI")  # Patch OpenAI client
@patch("agent_tooling.openai_client.get_tools")  # Patch get_tools to control available functions
def test_call_tools_tag_filtering(mock_get_tools, mock_openai):
    # Arrange
    # Mock OpenAI response to pretend it selected alpha_tool
    mock_openai_instance = mock_openai.return_value
    mock_openai_instance.chat.completions.create.return_value = type("obj", (object,), {
        "choices": [
            type("choice", (object,), {
                "message": type("message", (object,), {
                    "tool_calls": [
                        type("tool_call", (object,), {
                            "function": type("function", (object,), {
                                "name": "alpha_tool",
                                "arguments": json.dumps({
                                "question": "Test Alpha",
                                "messages": [{"role": "user", "content": "Test Alpha"}],
                                }),
                            }),
                            "id": "id_alpha"
                        })
                    ]
                })
            })
        ]
    })()

    # Patch get_tools to only return alpha_tool
    mock_get_tools.return_value = (
        [
            {
                "type": "function",
                "function": {
                    "name": "alpha_tool",
                    "description": "Alpha tool",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "messages": {"type": "array"},
                        },
                        "required": ["question", "messages"],
                    },
                    "return_type": "string",
                }
            }
        ],
        {
            "alpha_tool": alpha_tool
        }
    )

    tooling = OpenAITooling(api_key="test-api-key", model="gpt-4o")

    # Act
    result = tooling.call_tools(messages=[{"role": "user", "content": "Test Alpha"}], tags=["alpha"])

    # Assert
    # Validate that OpenAI was called with only "alpha_tool"
    called_tools = mock_openai_instance.chat.completions.create.call_args[1]["tools"]
    called_tool_names = [tool["function"]["name"] for tool in called_tools]
    assert called_tool_names == ["alpha_tool"]