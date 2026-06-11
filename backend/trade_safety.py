from datetime import datetime, timezone

ALLOWED_TOKENS = {"BNB", "USDT"}

MAX_TRADE_AMOUNTS = {
    "BNB": 0.002,
    "USDT": 2.0,
}

MIN_SECONDS_BETWEEN_TRADES = 60


last_trade_time = None


def validate_trade_request(amount: str, from_token: str, to_token: str, quote_only: bool):
    global last_trade_time

    from_token = from_token.upper()
    to_token = to_token.upper()

    if from_token not in ALLOWED_TOKENS:
        return False, f"Blocked: from_token {from_token} is not allowed."

    if to_token not in ALLOWED_TOKENS:
        return False, f"Blocked: to_token {to_token} is not allowed."

    if from_token == to_token:
        return False, "Blocked: from_token and to_token cannot be the same."

    try:
        numeric_amount = float(amount)
    except ValueError:
        return False, "Blocked: amount must be numeric."

    max_allowed = MAX_TRADE_AMOUNTS.get(from_token)

    if max_allowed is None:
        return False, f"Blocked: no max trade rule for {from_token}."

    if numeric_amount <= 0:
        return False, "Blocked: amount must be greater than zero."

    if numeric_amount > max_allowed:
        return False, f"Blocked: {amount} {from_token} exceeds max allowed {max_allowed} {from_token}."

    if not quote_only and last_trade_time is not None:
        now = datetime.now(timezone.utc)
        seconds_since_last_trade = (now - last_trade_time).total_seconds()

        if seconds_since_last_trade < MIN_SECONDS_BETWEEN_TRADES:
            return False, f"Blocked: wait {MIN_SECONDS_BETWEEN_TRADES - int(seconds_since_last_trade)} seconds before another live trade."

    return True, "Trade request passed safety checks."


def mark_live_trade_executed():
    global last_trade_time
    last_trade_time = datetime.now(timezone.utc)