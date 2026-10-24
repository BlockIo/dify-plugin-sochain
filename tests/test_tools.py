import json
from unittest.mock import MagicMock, patch

import pytest
import requests
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from provider.sochain import SoChainProvider
from tools.get_address_summary import GetAddressSummaryTool
from tools.get_address_transactions import GetAddressTransactionsTool
from tools.get_balance import GetBalanceTool
from tools.get_block import GetBlockTool
from tools.get_network_info import GetNetworkInfoTool
from tools.get_transaction import GetTransactionTool
from tools.get_transaction_status import GetTransactionStatusTool

API = "https://sochain.com/api/v3"
DOGE_ADDRESS = "DGUzATWpGdehtujWNyM464LB9Zx7Ch1Z67"
TX_HASH = "484c94145e97c0b2dd96912c1f056c9e05c8d358ab96ea429c51039d75d0d3c4"


def response(status=200, body=None, headers=None):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    resp.headers = headers or {}
    if body is None:
        resp.json.side_effect = ValueError("not JSON")
    else:
        resp.json.return_value = body
    return resp


def success(data):
    return response(body={"status": "success", "data": data})


def make(tool_cls, api_key=None):
    """A tool instance with only what _invoke uses: the runtime credentials and the message helpers."""
    tool = tool_cls.__new__(tool_cls)
    tool.runtime = MagicMock(credentials={"api_key": api_key} if api_key is not None else {})
    tool.create_text_message = lambda text: ("text", text)
    tool.create_json_message = lambda data: ("json", data)
    return tool


def run(tool_cls, params, api_key=None):
    return list(make(tool_cls, api_key)._invoke(params))


@pytest.fixture
def mock_get():
    with patch("tools.client.requests.get") as get:
        yield get


def test_balance_keyless(mock_get):
    mock_get.return_value = success({"confirmed": "0.00059184", "unconfirmed": "0.00000000"})

    messages = run(GetBalanceTool, {"network": "BTCTEST", "address": "tb1qtest0"})

    assert messages[0] == ("json", {"confirmed": "0.00059184", "unconfirmed": "0.00000000"})
    assert json.loads(messages[1][1]) == {"confirmed": "0.00059184", "unconfirmed": "0.00000000"}
    assert mock_get.call_args.args[0] == f"{API}/balance/BTCTEST/tb1qtest0"
    assert "API-KEY" not in mock_get.call_args.kwargs["headers"]
    assert mock_get.call_args.kwargs["timeout"] == 30


def test_api_key_sent_as_header(mock_get):
    mock_get.return_value = success({})

    run(GetNetworkInfoTool, {"network": "LTC"}, api_key="test-key")

    assert mock_get.call_args.kwargs["headers"]["API-KEY"] == "test-key"


def test_empty_api_key_is_keyless(mock_get):
    mock_get.return_value = success({})

    run(GetNetworkInfoTool, {"network": "LTC"}, api_key="  ")

    assert "API-KEY" not in mock_get.call_args.kwargs["headers"]


@pytest.mark.parametrize(
    "tool_cls, params, path",
    [
        (GetAddressSummaryTool, {"network": "doge", "address": DOGE_ADDRESS}, f"address_summary/DOGE/{DOGE_ADDRESS}"),
        (
            GetAddressTransactionsTool,
            {"network": "DOGE", "address": DOGE_ADDRESS},
            f"transactions/DOGE/{DOGE_ADDRESS}/1",
        ),
        (
            GetAddressTransactionsTool,
            {"network": "DOGE", "address": DOGE_ADDRESS, "page": 3.0},
            f"transactions/DOGE/{DOGE_ADDRESS}/3",
        ),
        (GetTransactionTool, {"network": "DOGE", "tx_hash": TX_HASH}, f"transaction/DOGE/{TX_HASH}"),
        (GetTransactionStatusTool, {"network": "ZEC", "tx_hash": TX_HASH}, f"transaction_status/ZEC/{TX_HASH}"),
        (GetBlockTool, {"network": "BTC", "block": "840000"}, "block/BTC/840000"),
        (GetBlockTool, {"network": "BTC", "block": 840000.0}, "block/BTC/840000"),
        (GetNetworkInfoTool, {"network": "DOGETEST"}, "network_info/DOGETEST"),
    ],
)
def test_paths(mock_get, tool_cls, params, path):
    mock_get.return_value = success({})

    run(tool_cls, params)

    assert mock_get.call_args.args[0] == f"{API}/{path}"


def test_block_leaves_out_transaction_ids_unless_asked(mock_get):
    mock_get.return_value = success({"height": 1, "num_txs": 1, "txs": ["a" * 64]})
    assert run(GetBlockTool, {"network": "BTC", "block": "1"})[0] == ("json", {"height": 1, "num_txs": 1})

    mock_get.return_value = success({"height": 1, "num_txs": 1, "txs": ["a" * 64]})
    messages = run(GetBlockTool, {"network": "BTC", "block": "1", "include_transactions": True})
    assert messages[0][1]["txs"] == ["a" * 64]


@pytest.mark.parametrize(
    "tool_cls, params",
    [
        (GetNetworkInfoTool, {"network": "ETH"}),
        (GetBalanceTool, {"network": "BTC", "address": "../account_info"}),
        (GetBalanceTool, {"network": "BTC"}),
        (GetAddressTransactionsTool, {"network": "BTC", "address": "bc1qtest0", "page": 0}),
        (GetTransactionTool, {"network": "BTC", "tx_hash": "abc"}),
        (GetBlockTool, {"network": "BTC", "block": "latest"}),
    ],
)
def test_bad_input_sends_no_request(mock_get, tool_cls, params):
    messages = run(tool_cls, params)

    assert len(messages) == 1
    assert messages[0][0] == "text"
    assert messages[0][1].startswith("SoChain lookup failed: ")
    mock_get.assert_not_called()


def test_api_error_message(mock_get):
    mock_get.return_value = response(
        404, {"status": "fail", "data": {"error_message": "Unable to fetch address balance. Invalid address?"}}
    )

    messages = run(GetBalanceTool, {"network": "BTC", "address": "nope"})

    assert messages == [("text", "SoChain lookup failed: Unable to fetch address balance. Invalid address?")]


def test_bad_key_message(mock_get):
    mock_get.return_value = response(401, {"status": "fail", "data": {"error_message": "x"}})

    (message,) = run(GetNetworkInfoTool, {"network": "BTC"}, api_key="wrong")

    assert "did not accept the API key" in message[1]
    assert "https://sochain.com/dashboard" in message[1]


def test_rate_limit_message(mock_get):
    mock_get.return_value = response(429, {"status": "fail", "data": {}}, {"Retry-After": "20"})

    (message,) = run(GetNetworkInfoTool, {"network": "BTC"})

    assert "Try again in 20 seconds" in message[1]


def test_non_json_and_network_errors(mock_get):
    mock_get.return_value = response(502)
    assert run(GetNetworkInfoTool, {"network": "BTC"}) == [
        ("text", "SoChain lookup failed: SoChain answered HTTP 502.")
    ]

    mock_get.side_effect = requests.Timeout()
    (message,) = run(GetNetworkInfoTool, {"network": "BTC"})
    assert message[1] == "SoChain lookup failed: Could not reach SoChain: Timeout. Try again shortly."


def test_provider_accepts_no_key_without_a_request(mock_get):
    SoChainProvider.__new__(SoChainProvider)._validate_credentials({})
    SoChainProvider.__new__(SoChainProvider)._validate_credentials({"api_key": ""})
    mock_get.assert_not_called()


def test_provider_checks_a_key(mock_get):
    mock_get.return_value = success({"plan": "free"})
    SoChainProvider.__new__(SoChainProvider)._validate_credentials({"api_key": "good"})
    assert mock_get.call_args.args[0] == f"{API}/account_info"
    assert mock_get.call_args.kwargs["headers"]["API-KEY"] == "good"

    mock_get.return_value = response(401, {"status": "fail", "data": {}})
    with pytest.raises(ToolProviderCredentialValidationError):
        SoChainProvider.__new__(SoChainProvider)._validate_credentials({"api_key": "bad"})


def test_each_source_file_loads_one_class():
    """The plugin runtime loads exactly one Tool (or ToolProvider) subclass from each source file."""
    from pathlib import Path

    import yaml
    from dify_plugin import Tool, ToolProvider
    from dify_plugin.core.utils.class_loader import load_single_subclass_from_source

    root = Path(__file__).resolve().parents[1]
    provider = yaml.safe_load((root / "provider/sochain.yaml").read_text())
    load_single_subclass_from_source(
        module_name="provider.sochain",
        script_path=str(root / provider["extra"]["python"]["source"]),
        parent_type=ToolProvider,
    )
    assert len(provider["tools"]) == 7
    for tool_yaml in provider["tools"]:
        source = yaml.safe_load((root / tool_yaml).read_text())["extra"]["python"]["source"]
        load_single_subclass_from_source(
            module_name=source[:-3].replace("/", "."),
            script_path=str(root / source),
            parent_type=Tool,
        )
