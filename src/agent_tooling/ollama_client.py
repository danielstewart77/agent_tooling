import json
import httpx
import inspect
from typing import Any, Dict, List, Tuple, Generator, Union, Callable, Optional
from .tool import get_tool_schemas, get_tool_function, get_tool

def ollama_format_tools(tags: list[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Callable]]:
    functions = get_tool_schemas()
    tools = []
    available_functions = {}

    for function in functions:
        if tags and not any(tag in function.get("tags", []) for tag in tags):
            continue

        tools.append({
            "type": "function",
            "function": {
                "name": function["name"],
                "description": function["description"],
                "parameters": function["parameters"],
                "return_type": function.get("return_type", "string"),
            },
        })

        available_functions[function["name"]] = get_tool_function(function["name"])

    return tools, available_functions


class OllamaTooling:
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:8b",
        tool_choice: str = "auto",
        fallback_tool: Optional[Callable[[List[dict]], Union[str, Generator]]] = None
    ):
        self.base_url = base_url
        self.model = model
        self.tool_choice = tool_choice
        self.fallback_tool = fallback_tool

    def _post_chat(self, payload: dict) -> Generator[dict, None, None]:
        with httpx.stream("POST", f"{self.base_url}/api/chat", json=payload, timeout=60.0) as response:
            for line in response.iter_lines():
                if line.strip():
                    yield json.loads(line)

    def call_tools(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        tool_choice: Optional[str] = None,
        tags: Optional[List[str]] = None,
        fallback_tool: Optional[str] = None
    ) -> Generator[Union[str, dict], None, None]:
        model = model or self.model
        tool_choice = tool_choice or self.tool_choice

        if fallback_tool and get_tool(fallback_tool) is None:
            raise ValueError(f"Fallback tool '{fallback_tool}' not found.")

        tools, _ = ollama_format_tools(tags)

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "tools": tools,
            "tool_choice": tool_choice
        }

        fallback_triggered = False
        tool_matched = False

        for data in self._post_chat(payload):
            message = data.get("message", {})
            tool_calls = message.get("tool_calls")

            if tool_calls:
                tool_matched = True  # ✅ Tool was used, no fallback needed

                for tool_call in tool_calls:
                    name = tool_call["function"]["name"]
                    args = tool_call["function"]["arguments"]

                    if isinstance(args, str):
                        args = json.loads(args)

                    schema, func_map = get_tool(name)
                    valid_keys = set(schema[0]["parameters"]["properties"].keys())
                    invalid_keys = [k for k in args if k not in valid_keys]
                    if invalid_keys:
                        raise ValueError(
                            f"Tool '{name}' received unexpected keys: {invalid_keys}. "
                            f"Expected: {sorted(valid_keys)}"
                        )

                    function_to_call = func_map[name]
                    args.pop("messages", None)
                    sig = inspect.signature(function_to_call)

                    result = (
                        function_to_call(**args, messages=messages)
                        if "messages" in sig.parameters else
                        function_to_call(**args)
                    )

                    if isinstance(result, Generator):
                        yield from result
                    else:
                        message = {
                            "role": "function",
                            "tool_call_id": tool_call.get("id"),
                            "name": name,
                            "content": result
                        }
                        
                        messages.append(message)
                    return messages

            elif message.get("content") and not tool_matched:
                # Ignore premature content unless fallback is not defined
                if not fallback_tool:
                    yield message["content"]

        # If no tools were called, trigger fallback
        if not tool_matched and fallback_tool:
            fallback_triggered = True
            _, func_map = get_tool(fallback_tool)
            fallback_fn = func_map[next(iter(func_map))]
            result = fallback_fn(messages=messages)

            yield from result if isinstance(result, Generator) else [result]

        # Edge case: No tool matched and no fallback set
        if not tool_matched and not fallback_triggered and not fallback_tool:
            yield {
                "role": "assistant",
                "content": "No tool could be found to complete this request."
            }