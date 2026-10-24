# SoChain

**Author:** sochain
**Version:** 0.0.1
**Type:** tool
**Source:** https://github.com/BlockIo/dify-plugin-sochain
**Contact:** support@sochain.com

## Description

[SoChain](https://sochain.com) is a block explorer and API for Bitcoin, Litecoin, Dogecoin and Zcash. This plugin adds seven read-only lookup tools to Dify:

| Tool | Returns |
| --- | --- |
| Get Balance | Confirmed balance and pending change of an address |
| Get Address Summary | Balances, total received, transactions sent and received, first and last activity |
| Get Address Transactions | An address's transactions, ten per page, newest first |
| Get Transaction | A transaction's confirmations, block, fee, inputs and outputs |
| Get Transaction Status | Whether a transaction is pending, mined, replaced or dropped |
| Get Block | A block by height or hash: time, size, reward, fees, fee rates |
| Get Network Info | Newest block, hashrate, mempool and projected fee rates |

Every tool takes a network: `BTC`, `LTC`, `DOGE`, `ZEC`, or a testnet: `BTCTEST` (Bitcoin testnet4), `LTCTEST`, `DOGETEST`, `ZECTEST`. Amounts are decimal strings in coin units. The plugin only reads public blockchain data; it cannot send, sign or broadcast anything.

## Setup

1. Install the SoChain plugin from the Dify Marketplace.
2. Open **Tools > SoChain > Authorize**. The API key is optional:
   - Leave it empty to use SoChain without a key, up to a daily limit per IP address.
   - For a higher limit, sign in at [sochain.com/dashboard](https://sochain.com/dashboard) (email only, no card for the free plan), create a key and paste it here. The key is checked when you save it. Plans are listed at [sochain.com/pricing](https://sochain.com/pricing).

## Usage

Add any SoChain tool to an Agent, Chatflow or Workflow. Examples of questions an agent can answer with them:

- "What is the balance of the Dogecoin address DGUzATWpGdehtujWNyM464LB9Zx7Ch1Z67?"
- "Has transaction 484c94145e97c0b2dd96912c1f056c9e05c8d358ab96ea429c51039d75d0d3c4 on DOGE confirmed, and what fee did it pay?"
- "What fee rate gets a Bitcoin transaction into the next block?"

| Parameter | Tools | Description |
| --- | --- | --- |
| Network | all | BTC, LTC, DOGE, ZEC, BTCTEST, LTCTEST, DOGETEST or ZECTEST. Required. |
| Address | balance, summary, transactions | The address, in full. |
| Transaction ID | transaction, status | 64 hex characters. |
| Page | transactions | From 1, ten per page. Default 1. |
| Block | block | Height (e.g. `840000`) or hash. |
| Include Transaction IDs | block | Also return every transaction ID in the block. Off by default. |

Each tool returns the API's data as JSON (for Workflow nodes) and as text (for the LLM). Errors come back as a text message: an unknown network or malformed input is refused before any request; an invalid key, a rate limit (with the wait time when SoChain gives one) or an unknown address or transaction says what to do next.

## Connection requirements

The plugin sends HTTPS GET requests to `https://sochain.com/api/v3` only. With a key, it is sent as the `API-KEY` header. The Dify plugin runtime needs outbound network access to `sochain.com`. Requests time out after 30 seconds.

API reference: [sochain.com/docs](https://sochain.com/docs).

## Development

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest tests
dify-plugin plugin package . -o sochain-0.0.1.difypkg
```

The `dify-plugin` CLI is the `dify-plugin-<os>-<arch>` binary from the [dify-plugin-daemon releases](https://github.com/langgenius/dify-plugin-daemon/releases).

## Privacy

See [PRIVACY.md](PRIVACY.md).
