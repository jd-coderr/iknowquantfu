import os
from twak_executor import clean_address, get_cli_wallet_address

# Historical address retained only as a display fallback. Live execution does NOT trust it.
DEFAULT_AGENT_WALLET_ADDRESS = "0x695b32DdB023f76dE3FE4de485F7C0131De4754C"


def get_configured_agent_address():
    return clean_address(os.getenv("AGENT_WALLET_ADDRESS")) or clean_address(os.getenv("TWAK_AGENT_ADDRESS")) or DEFAULT_AGENT_WALLET_ADDRESS


def get_live_twak_agent_address():
    return get_cli_wallet_address(chain="bsc", password=os.getenv("TWAK_WALLET_PASSWORD"))


def get_twak_status():
    configured = get_configured_agent_address()
    live = get_live_twak_agent_address()
    explicit_config = clean_address(os.getenv("AGENT_WALLET_ADDRESS")) or clean_address(os.getenv("TWAK_AGENT_ADDRESS"))
    matches = bool(live and configured and live.lower() == configured.lower())
    return {
        "status": "configured" if configured else "missing",
        "agent_address": configured,
        "configured_agent_address": configured,
        "configured_address_is_explicit": bool(explicit_config),
        "live_cli_agent_address": live,
        "cli_address_matches_configured": matches,
        "live_execution_ready": bool(explicit_config and live and matches),
        "chain": "BSC",
        "registration": "ready" if explicit_config and live and matches else "not_ready",
        "reason": (
            "Configured address matches the local TWAK signing wallet."
            if explicit_config and live and matches
            else "Set AGENT_WALLET_ADDRESS/TWAK_AGENT_ADDRESS and ensure it matches the local TWAK signing wallet before live trading."
        ),
    }


def validate_live_wallet_identity():
    status = get_twak_status()
    if not status.get("live_execution_ready"):
        return False, status.get("reason") or "TWAK wallet identity is not verified."
    return True, "TWAK signing wallet identity verified."
