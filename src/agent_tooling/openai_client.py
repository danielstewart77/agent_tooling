import json
import warnings
from openai import OpenAI
from typing import Any, Dict, List, Tuple, Generator, Union, Callable, Optional
from .tool import get_tool_schemas, get_tool_function, get_tool
import inspect

def openai_format_tools(tags: list[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Callable]]:
    """OpenAI tool schema wrapper with optional tag filtering."""
    functions = get_tool_schemas()
    tools = []
    available_functions = {}

    for function in functions:
        function_tags = function.get("tags", [])
        if tags and not any(tag in function_tags for tag in tags):
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

        func_name = function["name"]
        available_functions[func_name] = get_tool_function(func_name)

    return tools, available_functions


class OpenAITooling:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        tool_choice: str = "auto",
        fallback_tool: Optional[Callable[[List[dict]], Union[str, Generator]]] = None
    ):
        """
        :param api_key: Your OpenAI API key.
        :param model: Model to use (e.g., 'gpt-4').
        :param tool_choice: OpenAI `tool_choice` option ('auto', specific tool name, or 'none').
        :param fallback_tool: Optional function to call when no tools match. Should accept `messages` and return a string or generator.
        """
        self.api_key = api_key
        self.model = model
        self.tool_choice = tool_choice
        self.fallback_tool = fallback_tool
        self._discovered_fallback: Optional[Callable] = None  # auto-discovered if needed

    def call_tools(
        self,
        messages: List[dict],
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        tool_choice: str = "auto",
        tags: Optional[List[str]] = None,
        fallback_tool: Optional[str] = None
    ) -> Generator:
        """
        Calls the OpenAI API with the provided messages and tools.
        :param messages: List of messages to send to the OpenAI API.
        :param api_key: OpenAI API key.
        :param model: Model to use (e.g., 'gpt-4').
        :param tool_choice: OpenAI `tool_choice` option ('auto', specific tool name, or 'none').
        :param tags: List of tags to filter tools.
        :param fallback_tool: Optional function to call when no tools match. Should accept `messages` and return a string or generator.
        :return: Generator yielding messages from the OpenAI API.
        """
        
        # validate that the fallback tool is a valid function
        if fallback_tool and get_tool(fallback_tool) is None:
            raise ValueError(f"Fallback tool '{fallback_tool}' not found.")
        if not api_key and not self.api_key:
            raise ValueError("API key is required.")
        
        if not api_key:
            api_key = self.api_key

        if not model and not self.model:
            raise ValueError("Model is required.")
        
        if not model:
            model = self.model

        client = OpenAI(api_key=api_key)
        tools, available_functions = openai_format_tools(tags=tags)

        completion =  client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice)
        
        response = completion.choices[0].message
        tool_calls = response.tool_calls

        if not tool_calls and fallback_tool:
            tool, _ = get_tool(fallback_tool)
            tools = [{
                "type": "function",
                "function": tool[0]
            }]

            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="required"  # force the fallback tool to be selected
            )

            response = completion.choices[0].message
            tool_calls = response.tool_calls

            # add the fallback tool to the available functions
            tool_schema, function = get_tool(fallback_tool)
            available_functions.update(function)

        if tool_calls:
            for tool_call in tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                # Validate args against schema
                tool_schema, function_map = get_tool(name)
                valid_keys = set(tool_schema[0]["parameters"]["properties"].keys())
                invalid_keys = [k for k in args if k not in valid_keys]
                if invalid_keys:
                    raise ValueError(
                        f"Tool '{name}' received unexpected argument(s): {invalid_keys}. "
                        f"Expected: {sorted(valid_keys)}"
                    )

                function_to_call = function_map[name]
                args.pop("messages", None)

                sig = inspect.signature(function_to_call)
                # we don't trust the llm to pass the messages verbatim
                # so if the function is expecting messages, we need to pass 
                # messages explicitly
                if "messages" in sig.parameters:
                    result = function_to_call(**args, messages=messages)
                else:
                    result = function_to_call(**args)

                if isinstance(result, Generator):
                    for part in result:
                        yield part
                else:
                    message = {
                    "role": "function",
                    "tool_call_id": tool_call.id,
                    "name": name,
                    "content": result}
                    messages.append(message)

            return messages
        
        messages.append({
            "role": "assistant",
            "content": "No tool could be found to complete this request."
        })
        return messages