import json
import os
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_TOKENS = {
    "USDT", "BNB", "ETH", "XRP", "DOGE", "LINK", "ADA", "AVAX", "UNI", "INJ",
    "CAKE", "TWT", "AAVE", "ATOM", "LTC", "DOT", "SHIB", "FIL", "FET",
    "PENDLE", "FLOKI", "1INCH",
}

MAX_TRADE_AMOUNTS = {
    "USDT": 5.0, "BNB": 0.002, "ETH": 0.002, "XRP": 5.0, "DOGE": 25.0,
    "LINK": 0.25, "ADA": 5.0, "AVAX": 0.25, "UNI": 0.5, "INJ": 0.25,
    "CAKE": 1.0, "TWT": 2.0, "AAVE": 0.05, "ATOM": 0.5, "LTC": 0.05,
    "DOT": 1.0, "SHIB": 250000.0, "FIL": 1.0, "FET": 5.0, "PENDLE": 1.0,
    "FLOKI": 75000.0, "1INCH": 10.0,
}
MIN_SECONDS_BETWEEN_TRADES = 60
STATE_DIR = Path(os.getenv("IKQF_STATE_DIR", str(Path(__file__).resolve().parent / "state"))).resolve()
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "trade_safety_state.json"


def normalize_token(value: str) -> str:
    token = str(value or "").upper().replace("/", "").replace("-", "").strip()
    if token == "USDT": return "USDT"
    if token.endswith("USDT"): token = token[:-4]
    return token or ""


def _load_last_trade_time():
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        raw = data.get("last_trade_time")
        return datetime.fromisoformat(raw) if raw else None
    except Exception:
        return None


def validate_trade_request(amount: str, from_token: str, to_token: str, quote_only: bool):
    from_token = normalize_token(from_token); to_token = normalize_token(to_token)
    if from_token not in ALLOWED_TOKENS: return False, f"Blocked: from_token {from_token} is not allowed."
    if to_token not in ALLOWED_TOKENS: return False, f"Blocked: to_token {to_token} is not allowed."
    if from_token == to_token: return False, "Blocked: from_token and to_token cannot be the same."
    if "USDT" not in {from_token, to_token}: return False, "Blocked: one side of every live route must be USDT."
    try: numeric_amount = float(amount)
    except (TypeError, ValueError): return False, "Blocked: amount must be numeric."
    max_allowed = MAX_TRADE_AMOUNTS.get(from_token)
    if max_allowed is None: return False, f"Blocked: no max trade rule for {from_token}."
    if numeric_amount <= 0: return False, "Blocked: amount must be greater than zero."
    if numeric_amount > max_allowed: return False, f"Blocked: {amount} {from_token} exceeds max allowed {max_allowed} {from_token}."
    if not quote_only:
        last_trade_time = _load_last_trade_time()
        if last_trade_time is not None:
            now = datetime.now(timezone.utc)
            if last_trade_time.tzinfo is None: last_trade_time = last_trade_time.replace(tzinfo=timezone.utc)
            seconds_since = (now - last_trade_time).total_seconds()
            if seconds_since < MIN_SECONDS_BETWEEN_TRADES:
                return False, f"Blocked: wait {MIN_SECONDS_BETWEEN_TRADES - int(seconds_since)} seconds before another live trade."
    return True, "Trade request passed safety checks."


def mark_live_trade_executed():
    STATE_FILE.write_text(json.dumps({"last_trade_time": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
