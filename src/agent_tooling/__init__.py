from .tool import tool, get_tool_schemas, get_tool_function, get_agents, Agent, get_tool, clear
from .openai_client import OpenAITooling
from .ollama_client import OllamaTooling
from .tool_discovery import discover_tools
__all__ = [
    'tool', 
    'get_tool_schemas', 
    'get_tool_function',
    'OpenAITooling',
    'get_agents',
    'Agent',
    'discover_tools',
    'get_tool',
    'OllamaTooling',
    'clear'
]

discover_tools()
