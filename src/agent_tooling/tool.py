import inspect
from functools import wraps

class ToolRegistry:
    """Manages function metadata registration."""

    def __init__(self):
        self.registered_tools = {}

    def tool(self, func):
        """Decorator to register a function with metadata."""
        sig = inspect.signature(func)
        
        param_details = {
            param: {"type": self._get_json_type(sig.parameters[param].annotation)}
            for param in sig.parameters
        }

        return_type = self._get_json_type(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else "null"

        self.registered_tools[func.__name__] = {
            "name": func.__name__,
            "description": func.__doc__ or "No description provided.",
            "parameters": {
                "type": "object",
                "properties": param_details,
                "required": list(param_details.keys())
            },
            "return_type": return_type
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def get_registered_tools(self):
        """Returns metadata for all registered functions."""
        return list(self.registered_tools.values())

    def _get_json_type(self, python_type):
        """Converts Python type annotations to JSON Schema types."""
        type_mapping = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        return type_mapping.get(python_type, "string")  # Default to string if unknown


# Create a singleton instance
tool_registry = ToolRegistry()
tool = tool_registry.tool  # Expose decorator
get_registered_tools = tool_registry.get_registered_tools  # Expose function
