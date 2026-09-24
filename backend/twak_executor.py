import json
import os
import re
import shutil
import subprocess
import threading
from typing import Optional


def clean_address(value: Optional[str]):
    if not value:
        return None
    value = str(value).strip()
    return value if re.fullmatch(r"0x[a-fA-F0-9]{40}", value) else None


def get_twak_base_command():
    if os.name == "nt":
        configured = os.getenv("TWAK_COMMAND")
        if configured:
            return [configured]
        legacy = r"C:\Users\oo\AppData\Roaming\npm\twak.cmd"
        if os.path.exists(legacy):
            return [legacy]
    if shutil.which("twak"):
        return ["twak"]
    return ["npx", "@trustwallet/cli"]


def _safe_command(cmd, password=None):
    text = " ".join(str(x) for x in cmd)
    return text.replace(password, "***") if password else text


def _extract_json(stdout: str):
    stdout = (stdout or "").strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except Exception:
        # Some CLI versions print a status line before JSON. Try the first JSON object/array.
        starts = [p for p in (stdout.find("{"), stdout.find("[")) if p >= 0]
        if not starts:
            return None
        start = min(starts)
        try:
            return json.loads(stdout[start:])
        except Exception:
            return None


def extract_portfolio_items(parsed):
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        for key in ("portfolio", "assets", "balances", "tokens"):
            value = parsed.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        for key in ("result", "data", "event"):
            nested = extract_portfolio_items(parsed.get(key))
            if nested:
                return nested
    return []


# The signer wallet does not change during a running backend process.
# Cache the verified CLI address so frontend status polling and each autonomous
# cycle do not launch overlapping `twak wallet address` subprocesses against
# the same wallet file. The cache resets naturally on deploy/restart.
_CLI_WALLET_ADDRESS_CACHE = {}
_CLI_WALLET_ADDRESS_LOCK = threading.Lock()


def get_cli_wallet_address(chain: str = "bsc", password: Optional[str] = None, force_refresh: bool = False):
    chain = str(chain or "bsc").strip().lower()

    if not force_refresh:
        cached = _CLI_WALLET_ADDRESS_CACHE.get(chain)
        if cached:
            return cached

    # Only one thread may interrogate the CLI wallet at a time. Without this,
    # the 10-second frontend status poll and the autonomous trading loop can
    # launch concurrent TWAK CLI processes and make the live cycle stall/fail.
    with _CLI_WALLET_ADDRESS_LOCK:
        if not force_refresh:
            cached = _CLI_WALLET_ADDRESS_CACHE.get(chain)
            if cached:
                return cached

        password = password or os.getenv("TWAK_WALLET_PASSWORD")
        cmd = [*get_twak_base_command(), "wallet", "address", "--chain", chain, "--json"]
        if password:
            cmd.extend(["--password", password])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        except Exception:
            return None

        parsed = _extract_json(result.stdout)
        candidates = []
        if isinstance(parsed, dict):
            candidates.extend([
                parsed.get("address"),
                (parsed.get("result") or {}).get("address")
                if isinstance(parsed.get("result"), dict) else None,
            ])
        candidates.append(result.stdout)

        for candidate in candidates:
            if not candidate:
                continue
            match = re.search(r"0x[a-fA-F0-9]{40}", str(candidate))
            if match:
                address = clean_address(match.group(0))
                if address:
                    _CLI_WALLET_ADDRESS_CACHE[chain] = address
                    return address

        return None


def clear_cli_wallet_address_cache(chain: Optional[str] = None):
    """Clear the process-local signer cache; mainly useful for diagnostics/tests."""
    with _CLI_WALLET_ADDRESS_LOCK:
        if chain is None:
            _CLI_WALLET_ADDRESS_CACHE.clear()
        else:
            _CLI_WALLET_ADDRESS_CACHE.pop(str(chain).strip().lower(), None)


def run_twak_swap(amount: str, from_token: str, to_token: str, chain: str = "bsc", slippage: str = "1", quote_only: bool = True, password: Optional[str] = None):
    cmd = [*get_twak_base_command(), "swap", str(amount), str(from_token), str(to_token), "--chain", chain, "--slippage", str(slippage), "--json"]
    if quote_only:
        cmd.append("--quote-only")
    if password:
        cmd.extend(["--password", password])
    safe_command = _safe_command(cmd, password)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        parsed = _extract_json(result.stdout)
        return {
            "success": result.returncode == 0,
            "command": safe_command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "parsed": parsed,
        }
    except subprocess.TimeoutExpired as error:
        return {"success": False, "command": safe_command, "stdout": error.stdout or "", "stderr": error.stderr or "TWAK swap timed out after 300 seconds.", "returncode": None, "error": "TIMEOUT"}
    except Exception as error:
        return {"success": False, "command": safe_command, "stdout": "", "stderr": str(error), "returncode": None, "error": "EXCEPTION"}


def run_twak_portfolio(address: Optional[str] = None, chain: str = "bsc", password: Optional[str] = None):
    """Read the portfolio of the *local signing wallet* and verify its identity.

    TWAK wallet portfolio operates on the local wallet; it is not an arbitrary-address
    portfolio RPC. Therefore we never pass --address. If a configured address is supplied,
    it is treated as the expected signing-wallet address and a mismatch is fatal.
    """
    expected_address = clean_address(address) or clean_address(os.getenv("AGENT_WALLET_ADDRESS")) or clean_address(os.getenv("TWAK_AGENT_ADDRESS"))
    password = password or os.getenv("TWAK_WALLET_PASSWORD")
    live_address = get_cli_wallet_address(chain=chain, password=password)

    if expected_address and live_address and expected_address.lower() != live_address.lower():
        return {
            "success": False,
            "portfolio": [],
            "address": live_address,
            "address_used": live_address,
            "expected_address": expected_address,
            "address_matches": False,
            "chain": chain,
            "message": "Configured agent address does not match the local TWAK signing wallet.",
        }

    cmd = [*get_twak_base_command(), "wallet", "portfolio", "--chains", chain, "--json"]
    if password:
        cmd.extend(["--password", password])
    safe_command = _safe_command(cmd, password)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as error:
        return {"success": False, "portfolio": [], "address": live_address, "address_used": live_address, "expected_address": expected_address, "address_matches": None if not expected_address or not live_address else False, "chain": chain, "stdout": "", "stderr": str(error), "returncode": None, "command": safe_command, "message": "TWAK portfolio command failed."}

    parsed = _extract_json(result.stdout)
    items = extract_portfolio_items(parsed)
    address_matches = None if not expected_address or not live_address else expected_address.lower() == live_address.lower()
    success = result.returncode == 0 and parsed is not None and (expected_address is None or address_matches is True)
    return {
        "success": success,
        "command": safe_command,
        "portfolio": items if success else [],
        "raw_portfolio_response": parsed,
        "address": live_address,
        "address_used": live_address,
        "expected_address": expected_address,
        "address_matches": address_matches,
        "chain": chain,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "message": "TWAK portfolio loaded from local signing wallet." if success else "TWAK portfolio lookup failed or wallet identity could not be verified.",
    }
