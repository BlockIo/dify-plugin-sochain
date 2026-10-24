from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.base import lookup
from tools.client import address, network, page


def path(p: dict[str, Any]) -> str:
    net, addr, number = network(p.get("network")), address(p.get("address")), page(p.get("page"))
    return f"transactions/{net}/{addr}/{number}"


class GetAddressTransactionsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        yield from lookup(self, tool_parameters, path)
