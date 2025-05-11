import pytest
import warnings

def test_get_tool_returns_none_for_missing():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = get_tool("unknown_func")
    assert result is None

from agent_tooling.tool import (
    tool,
    get_tool_schemas,
    get_tool_function,
    get_tool,
    clear,
)
from typing import Tuple, List, Dict, Callable, Any

# Run before each test
@pytest.fixture(autouse=True)
def run_before_each_test():
    clear()

def test_tool_is_registered():
    @tool
    def my_function(x: int) -> str:
        """Test function"""
        return str(x)

    assert any(f["name"] == "my_function" for f in get_tool_schemas())

def test_tool_with_tags_is_registered():
    @tool(tags=["some_tag"])
    def tagged_function(y: int) -> str:
        return str(y)

    schema = get_tool_schemas()
    assert schema[0]["tags"] == ["some_tag"]

def test_get_tool_schemas_returns_all():
    @tool
    def one(x: int) -> str: return str(x)

    @tool(tags=["tag1"])
    def two(y: int) -> str: return str(y)

    schemas = get_tool_schemas()
    assert len(schemas) == 2

def test_get_tool_schemas_by_tag_match():
    @tool(tags=["tagged"])
    def tagged() -> str: return "ok"

    @tool
    def plain() -> str: return "meh"

    filtered = get_tool_schemas(tags=["tagged"])
    assert len(filtered) == 1
    assert filtered[0]["name"] == "tagged"

def test_get_tool_schemas_by_tag_none():
    @tool(tags=["different_tag"])
    def another(): return "x"

    filtered = get_tool_schemas(tags=["missing_tag"])
    assert filtered == []

def test_get_tool_function_returns_callable():
    @tool
    def callable_func() -> str: return "test"

    fn = get_tool_function("callable_func")
    assert callable(fn)
    assert fn() == "test"

def test_get_tool_function_returns_none():
    fn = get_tool_function("nonexistent")
    assert fn is None

def test_get_tool_returns_schema_and_function():
    @tool
    def combo_func(a: int) -> str: return str(a)

    result = get_tool("combo_func")
    assert isinstance(result, tuple)
    schemas, funcs = result
    assert isinstance(schemas, list)
    assert isinstance(funcs, dict)
    assert "combo_func" in funcs

def test_get_tool_returns_none_for_missing():
    result = get_tool("unknown_func")
    assert result is None

def test_clear_empties_registry():
    @tool
    def dummy() -> str: return "clean"

    assert get_tool_function("dummy") is not None
    clear()
    assert get_tool_function("dummy") is None
    assert get_tool_schemas() == []
