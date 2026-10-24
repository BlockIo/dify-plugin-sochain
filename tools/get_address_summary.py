from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.base import lookup
from tools.client import address, network


def path(p: dict[str, Any]) -> str:
    return f"address_summary/{network(p.get('network'))}/{address(p.get('address'))}"


class GetAddressSummaryTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from lookup(self, tool_parameters, path)
