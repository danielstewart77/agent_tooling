# Agent Tooling

[![PyPI version](https://img.shields.io/pypi/v/agent_tooling.svg)](https://pypi.org/project/agent_tooling/)
[![License](https://img.shields.io/github/license/danielstewart77/agent_tooling.svg)](LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/agent_tooling.svg)](https://pypi.org/project/agent_tooling/)

A lightweight Python package for registering, discovering, and managing function metadata for OpenAI agents. Includes support for tagging, fallback tools, structured schema validation, and streaming.

---

## Installation

```bash
pip install agent_tooling
```

## Highlights

* ✅ Register tools with structured metadata and tags
* ✅ Auto-discover tools across packages with `discover_tools()`
* ✅ Generate OpenAI-compatible tool schemas
* ✅ Call tools with OpenAI's API using `OpenAITooling`
* ✅ Supports fallback tools and graceful degradation
* ✅ Validates function arguments against schema
* ✅ Smart message passing based on function signature
* ✅ Stream results or return all at once
* ✅ Expose registered agents and their code metadata

---

## Quick Start

```python
from agent_tooling import tool, get_tool_function, get_tool_schemas

@tool(tags=["math"])
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

schemas = get_tool_schemas()
func_dict = get_tool_function("add")
print(func_dict("a": 5, "b": 3))  # 8
```

---

## Example with OpenAITooling

```python
from agent_tooling import tool, OpenAITooling
import os

@tool(tags=["weather"])
def get_weather(location: str, unit: str = "celsius") -> str:
    """Returns mock weather for a location."""
    return f"The weather in {location} is sunny and 25°{unit[0].upper()}"

@tool(tags=["finance"])
def calculate_mortgage(principal: float, interest_rate: float, years: int) -> str:
    """Returns estimated monthly mortgage payment."""
    p, r, n = principal, interest_rate / 12, years * 12
    payment = (p * r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return f"Monthly payment: ${payment:.2f}"

openai = OpenAITooling(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")
messages = [{"role": "user", "content": "What's the weather in Paris and mortgage for $300,000 at 4.5% for 30 years?"}]

messages = openai.call_tools(messages, tags=["weather", "finance"])
for message in messages:
    if message["role"] == "function":
        print(f"{message['name']} → {message['content']}")
```

---

## Fallback Tool Example

```python
result_stream = openai.call_tools(
    messages=messages,
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4.1",
    tool_choice="auto",
    tags=["triage"],
    fallback_tool="web_search",
)

for response in result_stream:
    print(response["content"])
```

If the tools matching the provided tags cannot handle the message, the fallback tool will be automatically invoked.

---

## Example with OllamaTooling

Agent Tooling now supports the Ollama client! Use your local Ollama models in the same way as with the OpenAI API, including tool routing and fallback logic.

```python
from agent_tooling import tool, OllamaTooling

@tool(tags=["agent", "triage", "ollama", "openai"])
def summarize(text: str) -> str:
    """Short summary of provided text."""
    return text[:50] + "..." if len(text) > 50 else text

ollama_tooling_client = OllamaTooling(
    model="granite3.3:2b"  # Or another Ollama-hosted model
)

messages = [
    {"role": "user", "content": "Summarize this news article: <article text>"},
]

result_stream = ollama_tooling_client.call_tools(
    messages=messages,
    model="granite3.3:2b",
    tool_choice="auto",
    tags=["agent", "triage", "ollama"],
    fallback_tool="web_search",
)

for response in result_stream:
    print(response["content"])
```

This enables full function/tool chaining with models served by your local Ollama instance, and automatic fallback to other tools (like a web search) if required.

---

## API Reference

### `@tool(tags=None)`

Registers a function with introspected JSON schema + optional tags.

### `get_tool_schemas(tags=None) -> List[Dict[str, Any]]`

Returns OpenAI-compatible tool metadata (filtered by tag if provided).

### `get_tool_function(name) -> Optional[Callable]`

Returns function reference by name.

### `get_tool(name) -> Tuple[List[Dict[str, Any]], Dict[str, Callable]]`

Returns both the tool schema and function reference. Useful for fallback execution.

### `get_agents() -> List[Agent]`

Returns metadata + source code for each registered tool.

### `discover_tools(folders: list[str])`

Recursively imports all modules in specified package folders, auto-registering tools.

### `clear()`

Clears all registered tools and metadata.

---

### `OpenAITooling`

A helper class for integrating OpenAI tool-calling flows.

```python
OpenAITooling(api_key=None, model=None, tool_choice="auto")
```

#### Methods:

* `call_tools(messages, api_key=None, model=None, tool_choice="auto", tags=None, fallback_tool=None)`

  * Yields generator of response messages
  * If no tool matched, attempts a fallback if provided
  * Validates arguments and handles conditional message passing

---

### `OllamaTooling`

```python
OllamaTooling(model=None, tool_choice="auto")
```

#### Methods:

* `call_tools(messages, model=None, tool_choice="auto", tags=None, fallback_tool=None)`

  * Yields generator of response messages
  * If no tool matched, attempts a fallback if provided
  * Validates arguments and handles conditional message passing

---

## Manual Integration with OpenAI

```python
from openai import OpenAI
from agent_tooling import tool, get_tool_schemas, get_tool_function
import json

@tool(tags=["weather"])
def get_weather(location: str) -> str:
    return f"Weather in {location}: 25°C"

tools, _ = get_tool("get_weather")
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto",
)

for call in response.choices[0].message.tool_calls:
    name = call.function.name
    args = json.loads(call.function.arguments)
    _, funcs = get_tool(name)
    func = funcs[name]
    print(func(**args))
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Repo

[https://github.com/danielstewart77/agent\_tooling](https://github.com/danielstewart77/agent_tooling)