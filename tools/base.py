import json
from collections.abc import Callable, Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.client import SoChainError, get


def lookup(
    tool: Tool,
    params: dict[str, Any],
    path: Callable[[dict[str, Any]], str],
    shape: Callable[[Any, dict[str, Any]], Any] | None = None,
) -> Generator[ToolInvokeMessage, None, None]:
    """Run one SoChain lookup for ``tool`` and yield its JSON and text messages.

    Each tool file defines exactly one Tool subclass (the plugin loader requires it),
    so the shared steps live in this function rather than in a base class.
    """
    credentials = tool.runtime.credentials if tool.runtime else None
    api_key = (credentials or {}).get("api_key")
    try:
        data = get(path(params), api_key)
        if shape is not None:
            data = shape(data, params)
    except SoChainError as e:
        yield tool.create_text_message(f"SoChain lookup failed: {e}")
        return
    if isinstance(data, dict):
        yield tool.create_json_message(data)
    yield tool.create_text_message(json.dumps(data, ensure_ascii=False))
