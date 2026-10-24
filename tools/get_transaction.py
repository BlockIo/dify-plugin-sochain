from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.base import lookup
from tools.client import network, tx_hash


def path(p: dict[str, Any]) -> str:
    return f"transaction/{network(p.get('network'))}/{tx_hash(p.get('tx_hash'))}"


class GetTransactionTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from lookup(self, tool_parameters, path)
