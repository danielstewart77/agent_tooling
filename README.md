# Agent Tooling

A lightweight Python package for registering and managing function metadata.

## Installation

```bash
pip install agent_tooling
```

## Usage

```python
from agent_tooling import tool, get_registered_tools

@tool
def add_numbers(a: int, b: int) -> int:
    """Simple function to add two numbers."""
    return a + b

# Get registered tool metadata
tools = get_registered_tools()
print(tools)
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