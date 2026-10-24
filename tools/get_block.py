from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.base import lookup
from tools.client import block_id, network


def path(p: dict[str, Any]) -> str:
    return f"block/{network(p.get('network'))}/{block_id(p.get('block'))}"


def without_txs(data: Any, p: dict[str, Any]) -> Any:
    """Leave out the block's transaction IDs (often thousands) unless asked for."""
    if isinstance(data, dict) and not p.get("include_transactions"):
        return {k: v for k, v in data.items() if k != "txs"}
    return data


class GetBlockTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from lookup(self, tool_parameters, path, without_txs)
