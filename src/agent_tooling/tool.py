import inspect
from functools import wraps

class ToolRegistry:
    """Manages function metadata registration."""

    def __init__(self):
        self.registered_tools = {}

    def tool(self, func):
        """Decorator to register a function with metadata."""
        sig = inspect.signature(func)
        param_details = {param: str(sig.parameters[param].annotation) for param in sig.parameters}
        
        self.registered_tools[func.__name__] = {
            "name": func.__name__,
            "description": func.__doc__ or "No description provided.",
            "parameters": param_details,
            "return_type": str(sig.return_annotation) if sig.return_annotation != inspect.Signature.empty else "None"
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper

    def get_registered_tools(self):
        """Returns metadata for all registered functions."""
        return list(self.registered_tools.values())

# Create a singleton instance
tool_registry = ToolRegistry()
tool = tool_registry.tool  # Expose decorator
get_registered_tools = tool_registry.get_registered_tools  # Expose function
