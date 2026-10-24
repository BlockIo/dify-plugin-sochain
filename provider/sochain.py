from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tools.client import SoChainError, get


class SoChainProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        api_key = str(credentials.get("api_key") or "").strip()
        if not api_key:
            # The key is optional: without one the tools run keyless.
            return
        try:
            # /account_info needs a key and answers 401 for one SoChain doesn't accept.
            get("account_info", api_key)
        except SoChainError as e:
            raise ToolProviderCredentialValidationError(str(e)) from e
