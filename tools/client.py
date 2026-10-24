"""Calls to the SoChain API v3 (https://sochain.com/docs) and readable errors."""

import re
from typing import Any

import requests

API_BASE = "https://sochain.com/api/v3"
TIMEOUT_SECONDS = 30
DASHBOARD_URL = "https://sochain.com/dashboard"

NETWORKS = ("BTC", "LTC", "DOGE", "ZEC", "BTCTEST", "LTCTEST", "DOGETEST", "ZECTEST")

_ADDRESS = re.compile(r"^[A-Za-z0-9]{1,1000}$")
_TX_HASH = re.compile(r"^[0-9a-fA-F]{64}$")
_BLOCK = re.compile(r"^([0-9]{1,8}|[0-9a-fA-F]{64})$")


class SoChainError(Exception):
    pass


def network(value: Any) -> str:
    code = str(value or "").strip().upper()
    if code not in NETWORKS:
        raise SoChainError(f"Unknown network {value!r}. Use one of: {', '.join(NETWORKS)}.")
    return code


def address(value: Any) -> str:
    text = str(value or "").strip()
    if not _ADDRESS.match(text):
        raise SoChainError("An address is letters and digits only.")
    return text


def tx_hash(value: Any) -> str:
    text = str(value or "").strip()
    if not _TX_HASH.match(text):
        raise SoChainError("A transaction ID is 64 hex characters.")
    return text


def block_id(value: Any) -> str:
    text = str(value if value is not None else "").strip()
    if text.endswith(".0") and text[:-2].isdigit():
        # Number parameters can arrive as floats.
        text = text[:-2]
    if not _BLOCK.match(text):
        raise SoChainError("A block is a height (up to 8 digits) or a 64 hex character hash.")
    return text


def page(value: Any) -> int:
    if value in (None, ""):
        return 1
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        raise SoChainError("Page must be a whole number from 1.") from None
    if not 1 <= number <= 999999:
        raise SoChainError("Page must be a whole number from 1 to 999999.")
    return number


def error_message(status: int, body: Any, headers: Any) -> str:
    detail = ""
    if isinstance(body, dict) and isinstance(body.get("data"), dict):
        detail = str(body["data"].get("error_message") or "")
    if status == 401:
        return (
            "SoChain did not accept the API key. "
            f"Check the key in the plugin credentials or create one at {DASHBOARD_URL}."
        )
    if status == 429:
        retry_after = headers.get("Retry-After") if headers else None
        wait = f" Try again in {retry_after} seconds." if retry_after else " Try again later."
        return f"SoChain rate limit reached.{wait} An API key from {DASHBOARD_URL} raises the limit."
    if detail:
        return detail
    return f"SoChain answered HTTP {status}."


def get(path: str, api_key: str | None = None) -> Any:
    """GET an API v3 path and return the response's ``data``."""
    headers = {"Accept": "application/json", "User-Agent": "sochain-dify-plugin/0.0.1"}
    key = (api_key or "").strip()
    if key:
        headers["API-KEY"] = key
    try:
        response = requests.get(f"{API_BASE}/{path}", headers=headers, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as e:
        raise SoChainError(f"Could not reach SoChain: {type(e).__name__}. Try again shortly.") from e

    try:
        body = response.json()
    except ValueError:
        body = None
    if response.status_code >= 400 or not isinstance(body, dict) or body.get("status") != "success":
        raise SoChainError(error_message(response.status_code, body, response.headers))
    return body.get("data")
