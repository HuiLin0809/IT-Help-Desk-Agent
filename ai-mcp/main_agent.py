"""
Main Gemini + MCP Orchestrator

This script launches a local MCP server named `mcp_server.py`, discovers its
tools, exposes those tools to Gemini, and runs a simple command-line chat loop.

Expected project layout:
    your_project/
      main_agent.py
      mcp_server.py
      .env

Required packages:
    pip install google-genai mcp python-dotenv

Required .env value:
    GEMINI_API_KEY="your-gemini-api-key"

Run:
    python main_agent.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


MODEL_NAME = "gemini-1.5-flash"
MAX_TOOL_ROUNDS = 8


def _require_env(name: str) -> str:
    """Fail early with a clear error when a required environment variable is missing."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _schema_to_dict(schema: Any) -> dict[str, Any]:
    """Convert MCP/Pydantic schema objects into plain dictionaries."""
    if schema is None:
        return {"type": "object", "properties": {}}
    if isinstance(schema, dict):
        return schema
    if hasattr(schema, "model_dump"):
        return schema.model_dump(by_alias=True, exclude_none=True)
    return dict(schema)


def _sanitize_schema_for_gemini(schema: Any) -> Any:
    """
    Trim JSON Schema features that commonly appear in MCP schemas but are not
    part of Gemini's function declaration subset.

    FastMCP often emits optional strings as anyOf: [{type: string}, {type: null}].
    Gemini does not need the nullable branch when the field is absent from
    `required`, so this function keeps the concrete branch.
    """
    if isinstance(schema, list):
        return [_sanitize_schema_for_gemini(item) for item in schema]

    if not isinstance(schema, dict):
        return schema

    schema = dict(schema)

    for union_key in ("anyOf", "oneOf"):
        variants = schema.pop(union_key, None)
        if variants:
            non_null_variants = [
                variant for variant in variants if variant.get("type") != "null"
            ]
            if len(non_null_variants) == 1:
                merged = {**schema, **non_null_variants[0]}
                return _sanitize_schema_for_gemini(merged)

    for unsupported_key in (
        "$schema",
        "$defs",
        "definitions",
        "additionalProperties",
        "title",
        "default",
    ):
        schema.pop(unsupported_key, None)

    if "properties" in schema:
        schema["properties"] = {
            name: _sanitize_schema_for_gemini(property_schema)
            for name, property_schema in schema["properties"].items()
        }

    if "items" in schema:
        schema["items"] = _sanitize_schema_for_gemini(schema["items"])

    return schema


def _mcp_tool_to_gemini_declaration(tool: Any) -> types.FunctionDeclaration:
    """Translate one MCP tool definition into one Gemini function declaration."""
    input_schema = getattr(tool, "inputSchema", None)
    if input_schema is None:
        input_schema = getattr(tool, "input_schema", None)

    parameters = _sanitize_schema_for_gemini(_schema_to_dict(input_schema))
    parameters.setdefault("type", "object")
    parameters.setdefault("properties", {})

    return types.FunctionDeclaration(
        name=tool.name,
        description=tool.description or f"MCP tool: {tool.name}",
        parameters=parameters,
    )


def _extract_function_calls(response: Any) -> list[Any]:
    """Return all function calls Gemini requested in this model turn."""
    if getattr(response, "function_calls", None):
        return list(response.function_calls)

    calls: list[Any] = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            function_call = getattr(part, "function_call", None)
            if function_call:
                calls.append(function_call)
    return calls


def _mcp_tool_result_to_jsonable(result: Any) -> dict[str, Any]:
    """Convert an MCP call result into a compact JSON-serializable object."""
    content_items: list[dict[str, Any]] = []

    for item in getattr(result, "content", []) or []:
        if hasattr(item, "model_dump"):
            content_items.append(item.model_dump(by_alias=True, exclude_none=True))
        elif hasattr(item, "text"):
            content_items.append({"type": "text", "text": item.text})
        else:
            content_items.append({"type": type(item).__name__, "value": str(item)})

    return {
        "is_error": bool(getattr(result, "isError", False) or getattr(result, "is_error", False)),
        "content": content_items,
    }


def _print_response_text(response: Any) -> None:
    """Print Gemini's final user-facing response, with a small fallback."""
    text = getattr(response, "text", None)
    if text:
        print(f"\nAgent: {text}\n")
        return

    parts = []
    for candidate in getattr(response, "candidates", []) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", []) or []:
            if getattr(part, "text", None):
                parts.append(part.text)

    print(f"\nAgent: {' '.join(parts) if parts else '[No text response returned.]'}\n")


async def _generate_content(
    client: genai.Client,
    contents: Any,
    config: types.GenerateContentConfig,
) -> Any:
    """
    Run the synchronous google-genai call in a worker thread so the async MCP
    session remains responsive while Gemini is thinking.
    """
    return await asyncio.to_thread(
        client.models.generate_content,
        model=MODEL_NAME,
        contents=contents,
        config=config,
    )


async def process_user_message(
    client: genai.Client,
    session: ClientSession,
    config: types.GenerateContentConfig,
    user_message: str,
) -> None:
    """Send one user message to Gemini and fulfill any MCP tool calls it requests."""
    contents: list[Any] = [
        types.Content(role="user", parts=[types.Part(text=user_message)])
    ]

    for _ in range(MAX_TOOL_ROUNDS):
        response = await _generate_content(client, contents, config)
        function_calls = _extract_function_calls(response)

        if not function_calls:
            _print_response_text(response)
            return

        model_content = response.candidates[0].content
        contents.append(model_content)

        function_response_parts: list[types.Part] = []
        for function_call in function_calls:
            tool_name = function_call.name
            tool_args = dict(function_call.args or {})

            print(f"\n[Tool call] {tool_name}({json.dumps(tool_args, ensure_ascii=False)})")
            tool_result = await session.call_tool(tool_name, arguments=tool_args)
            jsonable_result = _mcp_tool_result_to_jsonable(tool_result)
            print(f"[Tool result] {json.dumps(jsonable_result, ensure_ascii=False)}")

            response_kwargs: dict[str, Any] = {
                "name": tool_name,
                "response": {"result": jsonable_result},
            }
            call_id = getattr(function_call, "id", None)
            if call_id:
                response_kwargs["id"] = call_id

            function_response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(**response_kwargs)
                )
            )

        contents.append(types.Content(role="tool", parts=function_response_parts))

    print(
        f"\nAgent: I stopped after {MAX_TOOL_ROUNDS} tool round(s) to avoid an infinite loop.\n"
    )


async def main() -> None:
    """Launch the MCP server, connect Gemini to its tools, and start the CLI loop."""
    load_dotenv()
    _require_env("GEMINI_API_KEY")

    client = genai.Client()

    server_script = Path(__file__).with_name("mcp_server.py")
    if not server_script.exists():
        raise FileNotFoundError(
            f"Expected MCP server at {server_script}. Put mcp_server.py next to main_agent.py."
        )

    server_params = StdioServerParameters(
        command=sys.executable or "python",
        args=[str(server_script)],
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_response = await session.list_tools()
            function_declarations = [
                _mcp_tool_to_gemini_declaration(tool)
                for tool in tools_response.tools
            ]

            print(
                "Connected to MCP server with tools:",
                ", ".join(declaration.name or "" for declaration in function_declarations),
            )

            gemini_tools = types.Tool(function_declarations=function_declarations)
            config = types.GenerateContentConfig(tools=[gemini_tools])

            print("Type your IT help desk request. Use 'exit' or 'quit' to stop.\n")
            while True:
                user_message = (await asyncio.to_thread(input, "You: ")).strip()
                if user_message.lower() in {"exit", "quit"}:
                    print("Goodbye.")
                    return
                if not user_message:
                    continue

                try:
                    await process_user_message(client, session, config, user_message)
                except KeyboardInterrupt:
                    print("\nGoodbye.")
                    return
                except Exception as exc:
                    print(f"\nAgent error: {exc}\n")


if __name__ == "__main__":
    asyncio.run(main())
