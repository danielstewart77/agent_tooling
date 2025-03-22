# Agent Tooling
A lightweight Python package for registering and managing function metadata and references, with built-in OpenAI integration.

## Installation
```bash
pip install agent_tooling
```

## Basic Usage
```python
from agent_tooling import tool, get_tool_schemas, get_tool_function

@tool
def add_numbers(a: int, b: int) -> int:
    """Simple function to add two numbers."""
    return a + b

# Get registered tool metadata
tool_schemas = get_tool_schemas()
print(tool_schemas)

# Get function reference by name
func = get_tool_function('add_numbers')
result = func(5, 3)  # Returns 8
```

## Example Output
```python
[{
    'name': 'add_numbers',
    'description': 'Simple function to add two numbers.',
    'parameters': {
        'type': 'object',
        'properties': {
            'a': {'type': 'integer'},
            'b': {'type': 'integer'}
        },
        'required': ['a', 'b']
    },
    'return_type': 'integer'
}]
```

## Features
- Easy function metadata registration
- Automatic introspection of function signatures
- Singleton tool registry
- JSON-schema compatible parameter definitions
- Function reference storage and retrieval
- Built-in OpenAI integration
- Compatible with AI tools frameworks

## API Reference

### `@tool`
Decorator to register a function as a tool, capturing its metadata and storing its reference.

### `get_tool_schemas()`
Returns a list of metadata schemas for all registered tools.

### `get_tool_function(name)`
Returns the function reference for a registered tool by name.

### `get_registered_tools()` (Deprecated)
Alias for `get_tool_schemas()` maintained for backward compatibility. Will be removed in a future version.

### `OpenAITooling`
A class that simplifies integration with OpenAI's API for tool use.

#### Constructor
```python
OpenAITooling(api_key: str = None, model: str = None, tool_choice: str = "auto")
```

#### Methods
- `call_tools(messages: list[dict[str, str]], api_key: str = None, model: str = None, tool_choice: str = "auto") -> dict`
  Handles OpenAI API tool calls and returns updated messages with tool results.

### `get_tools()`
Returns a tuple containing OpenAI-compatible tool schemas and available function references.

## Example with OpenAITooling Integration

```python
from agent_tooling import tool, OpenAITooling
import os

# Define your tools
@tool
def get_weather(location: str, unit: str = "celsius") -> str:
    """Get the current weather for a location."""
    # Implementation omitted
    return f"The weather in {location} is sunny and 25°{unit[0].upper()}"

@tool
def calculate_mortgage(principal: float, interest_rate: float, years: int) -> str:
    """Calculate monthly mortgage payment."""
    # Implementation omitted
    monthly_payment = (principal * (interest_rate/12) * (1 + interest_rate/12)**(years*12)) / ((1 + interest_rate/12)**(years*12) - 1)
    return f"Monthly payment: ${monthly_payment:.2f}"

# Initialize the OpenAI tooling
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAITooling(api_key=OPENAI_API_KEY, model="gpt-4o")

# Create a conversation
messages = [
    {"role": "user", "content": "What's the weather in Paris and how much would a $300,000 mortgage cost at 4.5% interest for 30 years?"}
]

# Process the request with tools
messages = openai.call_tools(messages=messages)

# Display the final response
for message in messages:
    if message["role"] == "function":
        print(f"Tool {message['name']} returned: {message['content']}")
```

## Manual OpenAI Integration

If you prefer to handle the OpenAI integration yourself:

```python
from agent_tooling import tool, get_tool_schemas, get_tool_function
from openai import OpenAI
import json

@tool
def get_weather(location: str, unit: str = "celsius") -> str:
    """Get the current weather for a location."""
    # Implementation omitted
    return f"The weather in {location} is sunny and 25°{unit[0].upper()}"

# Get tool schemas for AI model
tools = get_tool_schemas()

# Create AI client
client = OpenAI()

# Send request to AI with tools
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto",
)

# Process tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        # Get and call the function
        function_to_call = get_tool_function(name)
        result = function_to_call(**args)
        print(result)  # "The weather in Paris is sunny and 25°C"
```