"""CoinMarketCap x402 paid market-data client.

This Python wrapper calls the Node/TypeScript x402 client in cmc_x402_client.mjs.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

CMC_X402_QUOTES_URL = "https://pro-api.coinmarketcap.com/x402/v3/cryptocurrency/quotes/latest"
X402_PAYMENT_NETWORK = "Base"
X402_PAYMENT_CHAIN_ID = 8453
X402_PAYMENT_ASSET = "USDC"
X402_EXPECTED_PRICE_USD = "0.01"


def env_flag(name: str, default: str = "false") -> bool:
    return str(os.getenv(name, default)).strip().lower() in {"1", "true", "yes", "on"}


def normalize_symbol(coin: str) -> str:
    symbol = str(coin or "ETH").upper().replace("USDT", "").replace("/", "").replace("-", "").strip()
    return symbol or "ETH"


def get_cmc_x402_quote(coin: str = "ETH") -> dict:
    symbol = normalize_symbol(coin)
    x402_enabled = env_flag("X402_ENABLED", "false")
    private_key = os.getenv("X402_EVM_PRIVATE_KEY") or os.getenv("EVM_PRIVATE_KEY")

    proof = {
        "enabled": x402_enabled,
        "configured": bool(private_key),
        "success": False,
        "paid": False,
        "used_in_decision": False,
        "provider": "CoinMarketCap",
        "protocol": "x402",
        "endpoint": CMC_X402_QUOTES_URL,
        "tool": "cryptocurrency quotes latest",
        "symbol": symbol,
        "payment_network": X402_PAYMENT_NETWORK,
        "payment_chain_id": X402_PAYMENT_CHAIN_ID,
        "payment_asset": X402_PAYMENT_ASSET,
        "expected_price_usd": X402_EXPECTED_PRICE_USD,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client": "node_typescript_official_cmc_flow",
    }

    if not x402_enabled:
        return {
            **proof,
            "status": "disabled",
            "message": "Set X402_ENABLED=true to allow paid CMC x402 requests. Disabled mode spends no USDC.",
        }

    if not private_key:
        return {
            **proof,
            "status": "not_configured",
            "message": "Set X402_EVM_PRIVATE_KEY or EVM_PRIVATE_KEY with a Base wallet funded with USDC.",
        }

    script_path = Path(__file__).resolve().parent / "cmc_x402_client.mjs"

    if not script_path.exists():
        return {
            **proof,
            "status": "missing_node_client",
            "message": "backend/cmc_x402_client.mjs is missing.",
        }

    try:
        completed = subprocess.run(
            ["node", str(script_path), symbol],
            capture_output=True,
            text=True,
            timeout=60,
            env=os.environ.copy(),
        )

        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()

        if not stdout:
            return {
                **proof,
                "status": "node_client_failed",
                "message": "Node x402 client produced no JSON output.",
                "returncode": completed.returncode,
                "stderr": stderr[:1000],
            }

        try:
            result = json.loads(stdout)
        except Exception:
            return {
                **proof,
                "status": "node_client_invalid_json",
                "message": "Node x402 client output was not valid JSON.",
                "returncode": completed.returncode,
                "stdout": stdout[:1000],
                "stderr": stderr[:1000],
            }

        return {
            **proof,
            **result,
            "enabled": x402_enabled,
            "configured": bool(private_key),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "returncode": completed.returncode,
            "stderr": stderr[:1000] if stderr else None,
        }

    except subprocess.TimeoutExpired:
        return {
            **proof,
            "status": "timeout",
            "message": "Node x402 client timed out.",
        }

    except Exception as error:
        return {
            **proof,
            "status": "error",
            "message": "CMC x402 TypeScript client call failed.",
            "error": str(error),
        }