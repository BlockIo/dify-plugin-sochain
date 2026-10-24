from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.base import lookup
from tools.client import network


def path(p: dict[str, Any]) -> str:
    return f"network_info/{network(p.get('network'))}"


class GetNetworkInfoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from lookup(self, tool_parameters, path)
