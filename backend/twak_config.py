import os
from twak_executor import clean_address, get_cli_wallet_address

# Historical address retained only for backward-compatible reference.
# It is NEVER treated as proof of the active signing wallet.
DEFAULT_AGENT_WALLET_ADDRESS = "0x695b32DdB023f76dE3FE4de485F7C0131De4754C"


def get_explicit_agent_address():
    return clean_address(os.getenv("AGENT_WALLET_ADDRESS")) or clean_address(os.getenv("TWAK_AGENT_ADDRESS"))


def get_live_twak_agent_address():
    return get_cli_wallet_address(chain="bsc", password=os.getenv("TWAK_WALLET_PASSWORD"))


def get_configured_agent_address():
    """Return the address the backend should use for this process.

    Priority:
    1. Explicit expected address, when configured.
    2. The actual local TWAK signing wallet detected by the CLI.
    3. Historical display fallback only when neither is available.

    Live execution never relies on item 3 because validate_live_wallet_identity()
    requires a real CLI signer.
    """
    explicit = get_explicit_agent_address()
    if explicit:
        return explicit
    live = get_live_twak_agent_address()
    return live or DEFAULT_AGENT_WALLET_ADDRESS


def get_twak_status():
    explicit = get_explicit_agent_address()
    live = get_live_twak_agent_address()

    # If the operator supplied an expected address, it must match the actual signer.
    # If no expected address was supplied, the verified local signer is authoritative.
    mismatch = bool(explicit and live and explicit.lower() != live.lower())
    ready = bool(live and not mismatch)
    effective = explicit or live

    if not live:
        reason = (
            "No local TWAK signing wallet could be verified. Ensure the persistent TWAK wallet is mounted "
            "and TWAK_WALLET_PASSWORD is set correctly."
        )
    elif mismatch:
        reason = (
            f"Configured agent address {explicit} does not match the local TWAK signing wallet {live}."
        )
    elif explicit:
        reason = "Configured address matches the local TWAK signing wallet."
    else:
        reason = "Local TWAK signing wallet detected and verified automatically."

    return {
        "status": "verified" if ready else "not_ready",
        "agent_address": effective,
        "configured_agent_address": explicit,
        "configured_address_is_explicit": bool(explicit),
        "auto_detected_signer_used": bool(live and not explicit),
        "live_cli_agent_address": live,
        "cli_address_matches_configured": (None if not explicit else bool(live and explicit.lower() == live.lower())),
        "live_execution_ready": ready,
        "chain": "BSC",
        "registration": "ready" if ready else "not_ready",
        "reason": reason,
        "historical_fallback_address": DEFAULT_AGENT_WALLET_ADDRESS,
    }


def validate_live_wallet_identity():
    status = get_twak_status()
    if not status.get("live_execution_ready"):
        return False, status.get("reason") or "TWAK wallet identity is not verified."
    return True, status.get("reason") or "TWAK signing wallet identity verified."
