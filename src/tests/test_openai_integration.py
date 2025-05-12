import pytest
import os
from agent_tooling.openai_client import OpenAITooling
from agent_tooling.tool import tool, clear
from typing import Generator
import re

from agent_tooling.tool_discovery import discover_tools

pytestmark = pytest.mark.test_openai_integration  # Mark all tests in this module as integration

def collect_return(gen):
    try:
        while True:
            next(gen)
    except StopIteration as e:
        return e.value

# Register non-streaming and streaming tools
@tool(tags=["test"])
def echo_tool(input: str, messages: list[dict]) -> str:
    """Call this tool when asked to test the echo tool."""
    print(f"echo_tool called with input: {input}")

    return "echo_tool"

@tool(tags=["stream"])
def stream_tool(input: str, messages: list[dict]) -> Generator[str, None, None]:
    """Call this tool when asked to test the streaming tool."""
    yield f"Streamed: {input}"

@tool
def untagged_tool(input: str, messages: list[dict]) -> str:
    """Call this tool when asked to test the untagged tool."""
    return "untagged_tool"

@tool(tags=["triage"])
def triage_tool(input: str, messages: list[dict]) -> str:
    """Call this tool when asked to triage."""
    return "correct triage"

@tool(tags=["incorrect_triage"])
def not_triage_tool(input: str, messages: list[dict]) -> str:
    """Call this tool when asked to triage."""
    return "incorrect triage"

@tool
def fallback_tool(messages: list[dict]) -> str:
    return "This is the fallback response."

# Integration fixtures
@pytest.fixture
def client():
    return OpenAITooling(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4.1",
        tool_choice="required"
    )

# ---- API call tests ----
def test_non_streaming_tool_call(client):
    discover_tools()
    messages = [{"role": "user", "content": "test the echo tool"}]
    result_gen = client.call_tools(
        messages,
        api_key=None,
        model="gpt-4.1",
        tool_choice="required",
        tags=["test"]
    )

    # Extract the returned message list
    output = collect_return(result_gen)

    print(f"non-streaming tool call output: {output}")
    assert isinstance(output, list)
    assert any("echo_tool" in m.get("name", "") or "called successfully" in m.get("content", "")
               for m in output if isinstance(m, dict))


def test_streaming_tool_call(client):
    messages = [{"role": "user", "content": "call the streaming tool"}]
    result = client.call_tools(
        messages,
        api_key=None,
        model="gpt-4.1",
        tool_choice="required",  # force tool usage
        tags=["stream"]
    )

    output = list(result)
    print(f"streaming output: {output}")

    # This time we're expecting raw streamed strings
    assert any(isinstance(o, str) and "Streamed:" in o for o in output)


# ---- Tag filtering ----
def test_all_tools_available_if_no_tags(client):
    discover_tools()
    messages = [{"role": "user", "content": "Please use the untagged_tool to handle this input."}]
    result_gen = client.call_tools(
        messages=messages,
        api_key=None,
        model="gpt-4.1",
        tool_choice="required",
        tags=None # No tags specified
    )

    output = collect_return(result_gen)
    print(f"output: {output}")

    assert isinstance(output, list)
    assert any("untagged_tool" in m.get("content", "") for m in output if isinstance(m, dict))



def test_only_triage_tagged_tools_available(client):
    discover_tools()
    messages = [{"role": "user", "content": "call the triage_tool"}]
    result_gen = client.call_tools(
        messages=messages,
        api_key=None,
        model="gpt-4.1",
        tool_choice="required",
        tags=["triage"]
    )

    output = collect_return(result_gen)
    print(f"triage output: {output}")

    assert isinstance(output, list)
    assert any("correct triage" in m.get("content", "") for m in output if isinstance(m, dict))
    assert all("incorrect triage" not in m.get("content", "") for m in output if isinstance(m, dict))


# ---- Fallback behavior ----
def test_fallback_no_tool_match(client):
    messages = [{"role": "user", "content": "Do something totally unsupported."}]
    result = client.call_tools(
        messages=messages,
        api_key=None,
        model="gpt-4.1",
        tool_choice="none",  # force no tools to be selected
        tags=None
    )

    output = collect_return(result)
    assert any("No tool could be found" in m.get("content", "") for m in output if isinstance(m, dict))

def test_fallback_function_executes(client):
    discover_tools()
    messages = [{"role": "user", "content": "Force fallback."}]
    result = client.call_tools(
        messages=messages,
        api_key=None,
        model="gpt-4.1",
        tool_choice="none",  # disables OpenAI selecting any tool
        tags=None,
        fallback_tool="fallback_tool"
    )

    output = collect_return(result)
    assert any("fallback" in m.get("content", "") for m in output if isinstance(m, dict))

# ---- Fallback validation error ----
def test_fallback_validation_fails(client):
    with pytest.raises(ValueError, match=re.escape("Fallback tool 'bad_tool' not found.")):
        messages = [{"role": "user", "content": "Try a bad fallback."}]
        list(client.call_tools(messages, api_key=None, model="gpt-4.1", tool_choice="auto", tags=None, fallback_tool="bad_tool"))
