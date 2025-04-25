import inspect
from functools import wraps

class ToolRegistry:
    """Manages function metadata and references registration."""

    def __init__(self):
        self.tool_schemas = {}
        self.tool_functions = {}

    def tool(self, tags=None):
        """Decorator factory to register a function as a tool with optional tags."""
        def decorator(func):
            sig = inspect.signature(func)

            param_details = {
                param: {"type": self._get_json_type(sig.parameters[param].annotation)}
                for param in sig.parameters
            }

            return_type = self._get_json_type(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else "null"

            self.tool_schemas[func.__name__] = {
                "name": func.__name__,
                "description": func.__doc__ or "No description provided.",
                "parameters": {
                    "type": "object",
                    "properties": param_details,
                    "required": list(param_details.keys())
                },
                "return_type": return_type,
                "tags": tags or []
            }

            # Store the actual function reference
            self.tool_functions[func.__name__] = func

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper
        
        return decorator

    def get_tool_schemas(self, tags=None):
        """Returns metadata schemas for registered tools, optionally filtered by tags."""
        schemas = list(self.tool_schemas.values())
        if tags is None:
            return schemas
        return [schema for schema in schemas if any(tag in schema.get("tags", []) for tag in tags)]

    def get_tool_function(self, name):
        """Returns the function reference by name."""
        return self.tool_functions.get(name)

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

# Expose functions
tool = tool_registry.tool
get_tool_schemas = tool_registry.get_tool_schemas
get_tool_function = tool_registry.get_tool_function
