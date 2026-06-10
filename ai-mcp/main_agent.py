from __future__ import annotations
import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import ClientSession


MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MAX_TOOL_ROUNDS = 8

def _schema_to_dict(schema: Any) -> dict[str, Any]:
    if schema is None: return {"type": "object", "properties": {}}
    if isinstance(schema, dict): return schema
    if hasattr(schema, "model_dump"): return schema.model_dump(by_alias=True, exclude_none=True)
    return dict(schema)

def _sanitize_schema_for_gemini(schema: Any) -> Any:
    if isinstance(schema, list): return [_sanitize_schema_for_gemini(item) for item in schema]
    if not isinstance(schema, dict): return schema
    schema = dict(schema)
    for union_key in ("anyOf", "oneOf"):
        variants = schema.pop(union_key, None)
        if variants:
            non_null_variants = [v for v in variants if v.get("type") != "null"]
            if len(non_null_variants) == 1:
                return _sanitize_schema_for_gemini({**schema, **non_null_variants[0]})
    for unsupported_key in ("$schema", "$defs", "definitions", "additionalProperties", "title", "default"):
        schema.pop(unsupported_key, None)
    if "properties" in schema:
        schema["properties"] = {k: _sanitize_schema_for_gemini(v) for k, v in schema["properties"].items()}
    if "items" in schema:
        schema["items"] = _sanitize_schema_for_gemini(schema["items"])
    return schema

def _mcp_tool_to_gemini_declaration(tool: Any) -> types.FunctionDeclaration:
    input_schema = getattr(tool, "input_schema", getattr(tool, "inputSchema", None))
    parameters = _sanitize_schema_for_gemini(_schema_to_dict(input_schema))
    parameters.setdefault("type", "object")
    parameters.setdefault("properties", {})
    return types.FunctionDeclaration(
        name=tool.name,
        description=tool.description or f"MCP tool: {tool.name}",
        parameters=parameters,
    )

def _extract_function_calls(response: Any) -> list[Any]:
    if getattr(response, "function_calls", None): return list(response.function_calls)
    calls = []
    for candidate in getattr(response, "candidates", []) or []:
        for part in getattr(candidate.content, "parts", []) or []:
            if getattr(part, "function_call", None):
                calls.append(part.function_call)
    return calls

def _mcp_tool_result_to_jsonable(result: Any) -> dict[str, Any]:
    items = []
    for item in getattr(result, "content", []) or []:
        if hasattr(item, "model_dump"): items.append(item.model_dump(by_alias=True, exclude_none=True))
        elif hasattr(item, "text"): items.append({"type": "text", "text": item.text})
        else: items.append({"type": type(item).__name__, "value": str(item)})
    return {"is_error": bool(getattr(result, "is_error", False)), "content": items}

async def _generate_content(client: genai.Client, contents: Any, config: types.GenerateContentConfig) -> Any:
    return await asyncio.to_thread(client.models.generate_content, model=MODEL_NAME, contents=contents, config=config)

async def _execute_core_agent_loop(session: ClientSession, contextualized_prompt: str, employee_id: str) -> str:
    """Executes the dynamic Gemini model turn loop over the live active SSE network channel connection."""
    client = genai.Client()
    
    tools_response = await session.list_tools()
    function_declarations = [_mcp_tool_to_gemini_declaration(t) for t in tools_response.tools]
    
    system_instruction = (
        f"You are a professional IT Help Desk agent grounded in enterprise database logs.\n"
        f"The current user interacting with you has Employee ID: {employee_id}.\n"
        f"Before answering any technical statement or complaint, you MUST call the `get_device_health` tool "
        f"with employee_id='{employee_id}' to cross-reference database fields first.\n"
        f"If troubleshooting fails or physical hardware defects are evident, call `escalate_hardware_ticket` immediately."
    )
    
    config = types.GenerateContentConfig(
        tools=[types.Tool(function_declarations=function_declarations)] if function_declarations else None,
        system_instruction=system_instruction
    )
    
    contents = [types.Content(role="user", parts=[types.Part(text=contextualized_prompt)])]
    
    for _ in range(MAX_TOOL_ROUNDS):
        response = await _generate_content(client, contents, config)
        function_calls = _extract_function_calls(response)
        
        if not function_calls:
            return getattr(response, "text", None) or "Analysis complete with no summary text."
            
        contents.append(response.candidates[0].content)
        function_response_parts = []
        
        for call in function_calls:
            try:
                tool_result = await session.call_tool(call.name, arguments=dict(call.args or {}))
                jsonable_result = _mcp_tool_result_to_jsonable(tool_result)
                function_response_parts.append(
                    types.Part(function_response=types.FunctionResponse(name=call.name, response={"result": jsonable_result}))
                )
            except Exception as e:
                function_response_parts.append(
                    types.Part(function_response=types.FunctionResponse(name=call.name, response={"error": str(e)}))
                )
        contents.append(types.Content(role="tool", parts=function_response_parts))
        
    return "The reasoning agent loop timed out before answering."

if __name__ == "__main__":
    print("Run app_api.py or mcp_server.py to initiate runtime processes.")