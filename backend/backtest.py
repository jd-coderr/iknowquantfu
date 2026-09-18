from market_data import fetch_binance_klines
import pandas as pd


DRAWDOWN_LIMIT = 30.0
INITIAL_EQUITY = 10000
MIN_TRADES_REQUIRED = 7


def normalize_symbol(coin: str):
    coin = coin.upper().replace("/", "").replace("-", "")

    if coin.endswith("USDT"):
        return coin

    return coin + "USDT"


def timeframe_to_binance(timeframe: str):
    mapping = {
        "1M": "1m",
        "5M": "5m",
        "15M": "15m",
        "1H": "1h",
        "4H": "4h",
        "1D": "1d",
    }

    key = str(timeframe or "").upper().strip()
    if key not in mapping:
        raise ValueError(
            f"Unsupported timeframe '{timeframe}'. "
            f"Supported values: {', '.join(mapping.keys())}."
        )

    return mapping[key]


def timeframe_to_minutes(timeframe: str):
    mapping = {
        "1M": 1,
        "5M": 5,
        "15M": 15,
        "1H": 60,
        "4H": 240,
        "1D": 1440,
    }

    return mapping.get(timeframe.upper(), 240)


def get_backtest_limit(timeframe: str):
    """
    Pull a larger sample where possible so Signal Frequency Analysis is useful.
    Binance's common REST limit is 1000 candles, so we stay inside that.
    """
    return 1000


def get_risk_settings(risk: str):
    risk = risk.lower()

    if risk == "low":
        return {
            "entry_level": 4.8,
            "smoothed_gate": 4.0,
            "take_profit_level": 2.0,
            "stop_extension": 1.5,
            "win_pnl": 1.5,
            "loss_pnl": -0.75,
            "fee_per_trade": 0.10,
            "slippage_per_trade": 0.05
        }

    if risk == "high":
        return {
            "entry_level": 3.6,
            "smoothed_gate": 3.0,
            "take_profit_level": 2.3,
            "stop_extension": 2.5,
            "win_pnl": 3.0,
            "loss_pnl": -1.5,
            "fee_per_trade": 0.10,
            "slippage_per_trade": 0.05
        }

    return {
        "entry_level": 4.2,
        "smoothed_gate": 3.6,
        "take_profit_level": 2.0,
        "stop_extension": 2.0,
        "win_pnl": 2.0,
        "loss_pnl": -1.0,
        "fee_per_trade": 0.10,
        "slippage_per_trade": 0.05
    }


def calculate_rsi(series, length=13):
    """TradingView-style RSI for the original TDI script.

    Pine uses ta.rsi(close, 13), which is Wilder/RMA based.
    This keeps the backend TDI fastMA closer to the TradingView white-label signals.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()
    avg_loss = loss.ewm(alpha=1 / length, adjust=False, min_periods=length).mean()

    rs = avg_gain / avg_loss.where(avg_loss != 0)
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50)


def build_indicators(df):
    df = df.copy()

    df["typical_price"] = (df["high"] + df["low"]) / 2
    df["pv"] = df["typical_price"] * df["volume"]
    df["cum_pv"] = df["pv"].cumsum()
    df["cum_volume"] = df["volume"].cumsum()
    df["vwap"] = df["cum_pv"] / df["cum_volume"]

    df["deviation"] = abs(df["typical_price"] - df["vwap"]) * 100 / df["typical_price"]
    df["smoothed_deviation"] = df["deviation"].rolling(21).mean()

    df["rsi"] = calculate_rsi(df["close"], 13)

    # Original TDI white-label sharkfin logic from the TradingView script:
    # fastMA = ta.sma(ta.rsi(close, 13), 2)
    # slowMA = ta.sma(ta.rsi(close, 13), 7)
    #
    # The real white label trade signals are ONLY:
    # buySignal  = sharkFinLong and fastMA_tf < 32
    # sellSignal = sharkFinShort and fastMA_tf > 68
    #
    # The turquoise crosses are wait markers, not trades.
    # No TDI Bollinger-band triggers.
    # No signal-line 68/32 exits.
    df["tdi_fast"] = df["rsi"].rolling(2).mean()
    df["tdi_slow"] = df["rsi"].rolling(7).mean()

    low_14 = df["low"].rolling(14).min()
    high_14 = df["high"].rolling(14).max()
    df["stoch_fast"] = ((df["close"] - low_14) / (high_14 - low_14)) * 100
    df["stoch_medium"] = df["stoch_fast"].rolling(5).mean()
    df["stoch_slow"] = df["stoch_fast"].rolling(14).mean()

    # EMA / MACD / Ichimoku values used by the Ichimoku MACD EMA Confluence strategy.
    df["ema_fast"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=200, adjust=False).mean()
    ema_12 = df["close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd_line"] = ema_12 - ema_26
    df["macd_signal"] = df["macd_line"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd_line"] - df["macd_signal"]

    conversion_length = 9
    base_length = 26
    span_b_length = 52
    displacement = 26
    df["ichi_conversion"] = (
        df["high"].rolling(conversion_length).max() +
        df["low"].rolling(conversion_length).min()
    ) / 2.0
    df["ichi_base"] = (
        df["high"].rolling(base_length).max() +
        df["low"].rolling(base_length).min()
    ) / 2.0
    df["ichi_span_a"] = (df["ichi_conversion"] + df["ichi_base"]) / 2.0
    df["ichi_span_b"] = (
        df["high"].rolling(span_b_length).max() +
        df["low"].rolling(span_b_length).min()
    ) / 2.0
    df["cloud_top"] = pd.concat(
        [df["ichi_span_a"].shift(displacement), df["ichi_span_b"].shift(displacement)],
        axis=1,
    ).max(axis=1)
    df["cloud_bottom"] = pd.concat(
        [df["ichi_span_a"].shift(displacement), df["ichi_span_b"].shift(displacement)],
        axis=1,
    ).min(axis=1)

    # FVG Channel approximation from the TradingView Pine logic.
    smooth_len = 20
    bull_fvgs = []
    bear_fvgs = []
    avg_bull = []
    avg_bear = []

    highs = df["high"].tolist()
    lows = df["low"].tolist()
    closes = df["close"].tolist()

    for index in range(len(df)):
        if index >= 2:
            if lows[index] > highs[index - 2] and closes[index - 1] > highs[index - 2]:
                bull_fvgs.append(highs[index - 2])

            if highs[index] < lows[index - 2] and closes[index - 1] < lows[index - 2]:
                bear_fvgs.append(lows[index - 2])

        close = closes[index]
        bull_fvgs = [level for level in bull_fvgs if close >= level]
        bear_fvgs = [level for level in bear_fvgs if close <= level]

        avg_bull.append(sum(bull_fvgs) / len(bull_fvgs) if bull_fvgs else None)
        avg_bear.append(sum(bear_fvgs) / len(bear_fvgs) if bear_fvgs else None)

    df["fvg_avg_bull"] = pd.Series(avg_bull, index=df.index)
    df["fvg_avg_bear"] = pd.Series(avg_bear, index=df.index)
    price_sma = df["close"].rolling(smooth_len).mean()
    bull_boundary_raw = df["fvg_avg_bull"].where(df["fvg_avg_bull"].notna(), price_sma)
    bear_boundary_raw = df["fvg_avg_bear"].where(df["fvg_avg_bear"].notna(), price_sma)
    df["fvg_upper_boundary"] = bear_boundary_raw.rolling(smooth_len).mean().rolling(smooth_len).mean()
    df["fvg_lower_boundary"] = bull_boundary_raw.rolling(smooth_len).mean().rolling(smooth_len).mean()
    df["fvg_upper_boundary"] = df["fvg_upper_boundary"].fillna(price_sma).fillna(df["close"])
    df["fvg_lower_boundary"] = df["fvg_lower_boundary"].fillna(price_sma).fillna(df["close"])

    fvg_bull_signals = []
    fvg_bear_signals = []
    bars_since_close_ge_lower = None
    bars_since_close_le_upper = None
    last_bull_bar = -10_000
    last_bear_bar = -10_000

    for index, row in df.iterrows():
        position = len(fvg_bull_signals)
        close = row["close"]
        lower = row["fvg_lower_boundary"]
        upper = row["fvg_upper_boundary"]

        if close >= lower:
            bars_since_close_ge_lower = 0
        elif bars_since_close_ge_lower is not None:
            bars_since_close_ge_lower += 1

        if close <= upper:
            bars_since_close_le_upper = 0
        elif bars_since_close_le_upper is not None:
            bars_since_close_le_upper += 1

        bull_signal = (
            bars_since_close_ge_lower is not None and
            bars_since_close_ge_lower >= 5 and
            (position - last_bull_bar) > 50
        )
        bear_signal = (
            bars_since_close_le_upper is not None and
            bars_since_close_le_upper >= 5 and
            (position - last_bear_bar) > 50
        )

        if bull_signal:
            last_bull_bar = position
        if bear_signal:
            last_bear_bar = position

        fvg_bull_signals.append(bool(bull_signal))
        fvg_bear_signals.append(bool(bear_signal))

    df["fvg_bull_signal"] = fvg_bull_signals
    df["fvg_bear_signal"] = fvg_bear_signals

    # Ichimoku MACD EMA Confluence signal state. Loose mode is the Pine default,
    # so the baseline signal is EMA direction + MACD direction, with state-change gating.
    trend_bull_signals = []
    trend_bear_signals = []
    last_signal = 0
    last_signal_bar = 0
    cooldown_bars = 0

    for index, row in df.reset_index(drop=True).iterrows():
        bullish_confluence = (
            row["macd_line"] > row["macd_signal"] and
            row["ema_fast"] > row["ema_slow"]
        )
        bearish_confluence = (
            row["macd_line"] < row["macd_signal"] and
            row["ema_fast"] < row["ema_slow"]
        )

        bull_signal = bullish_confluence and last_signal != 1 and (index - last_signal_bar > cooldown_bars)
        bear_signal = bearish_confluence and last_signal != -1 and (index - last_signal_bar > cooldown_bars)

        if bull_signal:
            last_signal = 1
            last_signal_bar = index
        elif bear_signal:
            last_signal = -1
            last_signal_bar = index

        trend_bull_signals.append(bool(bull_signal))
        trend_bear_signals.append(bool(bear_signal))

    df["trend_bull_signal"] = trend_bull_signals
    df["trend_bear_signal"] = trend_bear_signals

    df = df.bfill().ffill()

    return df



def get_tdi_sharkfin_state(df, index):
    """Original TDI white-label sharkfin signals from the uploaded Pine script.

    Pine logic:

    sharkFinLong =
        fastMA_tf[2] < 32
        and fastMA_tf[1] > fastMA_tf[2]
        and fastMA_tf > fastMA_tf[1]

    buySignal =
        sharkFinLong and fastMA_tf < 32

    sharkFinShort =
        fastMA_tf[2] > 68
        and fastMA_tf[1] < fastMA_tf[2]
        and fastMA_tf < fastMA_tf[1]

    sellSignal =
        sharkFinShort and fastMA_tf > 68

    These are the WHITE label signals.
    Turquoise crosses are ignored.
    """
    row = df.iloc[index]
    prev_1 = df.iloc[index - 1] if index >= 1 else row
    prev_2 = df.iloc[index - 2] if index >= 2 else row

    fast_0 = float(row.get("tdi_fast", 50))
    fast_1 = float(prev_1.get("tdi_fast", fast_0))
    fast_2 = float(prev_2.get("tdi_fast", fast_1))

    curling_up = fast_1 > fast_2 and fast_0 > fast_1
    curling_down = fast_1 < fast_2 and fast_0 < fast_1

    white_buy = fast_2 < 32 and curling_up and fast_0 < 32
    white_sell = fast_2 > 68 and curling_down and fast_0 > 68

    if white_buy:
        trigger = "tdi_white_buy_signal"
    elif white_sell:
        trigger = "tdi_white_sell_signal"
    else:
        trigger = "none"

    return {
        "long_entry": bool(white_buy),
        "short_entry": bool(white_sell),
        "white_buy": bool(white_buy),
        "white_sell": bool(white_sell),

        # Backward-compatible keys so older app/frontend reads do not crash.
        # Only white_buy and white_sell are valid triggers now.
        "fixed_long": bool(white_buy),
        "fixed_short": bool(white_sell),
        "bb_long": False,
        "bb_short": False,
        "signal_exit_long": False,
        "signal_exit_short": False,

        "trigger": trigger,
        "tdi_fast": round(fast_0, 4),
        "tdi_fast_prev_1": round(fast_1, 4),
        "tdi_fast_prev_2": round(fast_2, 4),
        "curling_up": bool(curling_up),
        "curling_down": bool(curling_down),
    }



def get_tdi_bottom_to_top_state(df, index, strategy=None):
    """Evaluate the executable IKQF TDI Bottom-to-Top strategy.

    The JSON describes four entry rules but does not define a numeric confidence
    formula. To keep the implementation deterministic and faithful to the rules,
    each of the four rule groups contributes 25 points. Because the strategy
    requires confidence above 80, all four rule groups must pass for entry.
    """
    strategy = strategy or {}
    indicator_settings = strategy.get("indicator_settings") or {}
    tdi_settings = indicator_settings.get("tdi") or {}

    lower_zone = float(tdi_settings.get("lower_zone", 32))
    upper_zone = float(tdi_settings.get("upper_zone", 68))

    row = df.iloc[index]
    prev_1 = df.iloc[index - 1] if index >= 1 else row
    prev_2 = df.iloc[index - 2] if index >= 2 else prev_1

    fast_0 = float(row.get("tdi_fast", 50))
    fast_1 = float(prev_1.get("tdi_fast", fast_0))
    fast_2 = float(prev_2.get("tdi_fast", fast_1))
    slow_0 = float(row.get("tdi_slow", 50))
    slow_1 = float(prev_1.get("tdi_slow", slow_0))

    # Rule 1: TDI reached the lower zone recently or formed the white-label
    # lower-zone sharkfin. Using the recent 3-bar window allows a reclaim of 32
    # to qualify on the candle immediately after the dip.
    recent_lower_extreme = min(fast_0, fast_1, fast_2) < lower_zone
    sharkfin_up = fast_2 < lower_zone and fast_1 > fast_2 and fast_0 > fast_1
    lower_extreme_ok = recent_lower_extreme or sharkfin_up

    # Rule 2: green/fast TDI crosses up red/slow TDI, reclaims 32, or continues
    # the explicit lower-zone sharkfin reversal.
    cross_up = fast_1 <= slow_1 and fast_0 > slow_0
    reclaim_lower = fast_1 <= lower_zone and fast_0 > lower_zone
    reversal_ok = cross_up or reclaim_lower or sharkfin_up

    close = float(row.get("close", 0))
    ema_fast = float(row.get("ema_fast", close))
    ema_slow = float(row.get("ema_slow", close))

    # Rule 3: reject a strong 50/200 EMA downtrend only when price is also below
    # the 200 EMA. This implements "price_not_below_200ema_in_strong_downtrend".
    strong_downtrend = ema_fast < ema_slow and close < ema_slow
    trend_ok = not strong_downtrend

    # Rule 4: reversal must have either above-average volume or a simple bullish
    # structure confirmation (close above the previous candle high).
    start = max(0, index - 20)
    volume_window = df["volume"].iloc[start:index]
    volume_avg = float(volume_window.mean()) if len(volume_window) else float(row.get("volume", 0))
    volume_confirm = float(row.get("volume", 0)) > volume_avg if volume_avg > 0 else True
    structure_confirm = close > float(prev_1.get("high", close))
    confirmation_ok = volume_confirm or structure_confirm

    checks = {
        "lower_extreme": bool(lower_extreme_ok),
        "reversal": bool(reversal_ok),
        "trend_filter": bool(trend_ok),
        "volume_or_structure": bool(confirmation_ok),
    }
    confidence = sum(25 for passed in checks.values() if passed)
    long_entry = confidence > 80

    # Stateless technical reduce-risk / exit signal for the live spot wallet.
    cross_down = fast_1 >= slow_1 and fast_0 < slow_0
    upper_reached = fast_0 >= upper_zone

    swing_start = max(0, index - 5)
    recent_structure_low = float(df["low"].iloc[swing_start:index].min()) if index > swing_start else float(row.get("low", close))
    structure_lost = close < recent_structure_low
    bearish_regime = ema_fast < ema_slow and close < ema_slow

    short_exit = bool(upper_reached or cross_down or structure_lost or bearish_regime)

    return {
        "long_entry": bool(long_entry),
        "short_exit": short_exit,
        "confidence_score": int(confidence),
        "entry_checks": checks,
        "tdi_fast": round(fast_0, 4),
        "tdi_fast_prev_1": round(fast_1, 4),
        "tdi_fast_prev_2": round(fast_2, 4),
        "tdi_slow": round(slow_0, 4),
        "lower_zone": lower_zone,
        "upper_zone": upper_zone,
        "cross_up": bool(cross_up),
        "cross_down": bool(cross_down),
        "reclaim_lower": bool(reclaim_lower),
        "sharkfin_up": bool(sharkfin_up),
        "volume_confirm": bool(volume_confirm),
        "structure_confirm": bool(structure_confirm),
        "strong_downtrend": bool(strong_downtrend),
        "upper_reached": bool(upper_reached),
        "structure_lost": bool(structure_lost),
        "bearish_regime": bool(bearish_regime),
    }


def get_signal(strategy_type, df, index, settings, strategy=None):
    row = df.iloc[index]
    prev_1 = df.iloc[index - 1] if index >= 1 else row
    prev_2 = df.iloc[index - 2] if index >= 2 else row

    if strategy_type == "mean_reversion":
        entry = (
            row["deviation"] >= settings["entry_level"] and
            row["smoothed_deviation"] >= settings["smoothed_gate"]
        )

        return "long" if entry else None

    if strategy_type == "trend_continuation":
        recent_high = df["high"].iloc[max(0, index - 20):index].max()
        volume_avg = df["volume"].iloc[max(0, index - 20):index].mean()

        bullish_break = row["close"] > recent_high
        volume_confirm = row["volume"] > volume_avg * 1.2

        return "long" if bullish_break and volume_confirm else None

    if strategy_type == "momentum_rotation":
        fast_turning_up = row["stoch_fast"] > prev_1["stoch_fast"] > prev_2["stoch_fast"]
        medium_up = row["stoch_medium"] > prev_1["stoch_medium"]
        slow_confirm = row["stoch_slow"] > 45

        return "long" if fast_turning_up and medium_up and slow_confirm else None

    if strategy_type == "tdi_signal_reversal":
        tdi_state = get_tdi_sharkfin_state(df, index)

        # Entries only. The signal-line 68/32 exits are handled separately while a trade is open.
        if tdi_state["long_entry"]:
            return "long"

        if tdi_state["short_entry"]:
            return "short"

        return None

    if strategy_type == "tdi_bottom_to_top_reversal":
        tdi_state = get_tdi_bottom_to_top_state(df, index, strategy=strategy)

        if tdi_state["long_entry"]:
            return "long"

        if tdi_state["short_exit"]:
            return "short"

        return None

    if strategy_type == "mean_reversion_channel":
        if bool(row.get("fvg_bull_signal", False)):
            return "long"

        if bool(row.get("fvg_bear_signal", False)):
            return "short"

        return None

    if strategy_type == "trend_confluence":
        if bool(row.get("trend_bull_signal", False)):
            return "long"

        if bool(row.get("trend_bear_signal", False)):
            return "short"

        return None

    return None


def calculate_drawdown_durations(equity_curve):
    durations = []
    current_duration = 0
    peak = INITIAL_EQUITY

    for value in equity_curve:
        if value >= peak:
            if current_duration > 0:
                durations.append(current_duration)
                current_duration = 0
            peak = value
        else:
            current_duration += 1

    if current_duration > 0:
        durations.append(current_duration)

    if not durations:
        return 0

    return sum(durations) / len(durations)


def calculate_sharpe_ratio(trade_returns):
    if len(trade_returns) < 2:
        return 0

    series = pd.Series(trade_returns)
    std = series.std()

    if std == 0:
        return 0

    return series.mean() / std


def calculate_sortino_ratio(trade_returns):
    if len(trade_returns) < 2:
        return 0

    series = pd.Series(trade_returns)
    downside = series[series < 0]

    if len(downside) < 2:
        return 0

    downside_deviation = ((downside ** 2).mean()) ** 0.5

    if downside_deviation == 0:
        return 0

    return series.mean() / downside_deviation

def calculate_activity_profile(trades, backtest_start, backtest_end):
    start = pd.to_datetime(backtest_start)
    end = pd.to_datetime(backtest_end)

    if pd.isna(start) or pd.isna(end) or end <= start:
        period_days = 0.0
    else:
        period_days = (end - start).total_seconds() / 86400

    total_trades = len(trades)
    safe_period_days = max(period_days, 1 / 24)
    signals_per_day_value = total_trades / safe_period_days if safe_period_days > 0 else 0.0

    entry_times = []
    for trade in trades:
        value = trade.get("entry_timestamp") or trade.get("entry_time")
        timestamp = pd.to_datetime(value, errors="coerce")
        if not pd.isna(timestamp):
            entry_times.append(timestamp)

    entry_times = sorted(entry_times)
    active_trade_days = {timestamp.date() for timestamp in entry_times}

    if period_days <= 0:
        total_calendar_days = 1
    else:
        total_calendar_days = max(1, len(pd.date_range(start.date(), end.date(), freq="D")))

    active_days_pct_value = (len(active_trade_days) / total_calendar_days) * 100 if total_calendar_days > 0 else 0.0

    if len(entry_times) >= 2:
        gaps_between = [
            (entry_times[index] - entry_times[index - 1]).total_seconds() / 3600
            for index in range(1, len(entry_times))
        ]
        avg_hours_between_signals_value = sum(gaps_between) / len(gaps_between)
    else:
        avg_hours_between_signals_value = None

    quiet_gaps = []
    if entry_times:
        quiet_gaps.append((entry_times[0] - start).total_seconds() / 3600)
        quiet_gaps.extend(
            (entry_times[index] - entry_times[index - 1]).total_seconds() / 3600
            for index in range(1, len(entry_times))
        )
        quiet_gaps.append((end - entry_times[-1]).total_seconds() / 3600)
    else:
        quiet_gaps.append(max(0.0, (end - start).total_seconds() / 3600))

    longest_quiet_gap_hours_value = max(quiet_gaps) if quiet_gaps else 0.0
    longest_quiet_gap_days_value = longest_quiet_gap_hours_value / 24

    if signals_per_day_value >= 5:
        trade_style = "HIGH FREQUENCY"
        activity_status = "VERY ACTIVE"
    elif signals_per_day_value >= 1:
        trade_style = "ACTIVE INTRADAY"
        activity_status = "ACTIVE"
    elif signals_per_day_value >= 0.5:
        trade_style = "MODERATE INTRADAY"
        activity_status = "MODERATE"
    elif signals_per_day_value >= 0.1:
        trade_style = "PATIENT / SWING"
        activity_status = "LOW FREQUENCY"
    elif signals_per_day_value > 0:
        trade_style = "RARE / CONFIRMATION"
        activity_status = "RARE"
    else:
        trade_style = "INACTIVE IN SAMPLE"
        activity_status = "NO SIGNALS"

    if longest_quiet_gap_days_value <= 1:
        quiet_gap_status = "CONSISTENT"
    elif longest_quiet_gap_days_value <= 3:
        quiet_gap_status = "INTERMITTENT"
    else:
        quiet_gap_status = "SPARSE"

    if period_days >= 14:
        sample_confidence = "HIGH"
    elif period_days >= 7:
        sample_confidence = "MEDIUM"
    else:
        sample_confidence = "LOW"

    return {
        "activity_status": activity_status,
        "trade_style": trade_style,
        "signals_per_day": f"{signals_per_day_value:.2f}",
        "signals_per_day_value": round(signals_per_day_value, 4),
        "active_days_pct": f"{active_days_pct_value:.2f}%",
        "active_days_pct_value": round(active_days_pct_value, 2),
        "active_trade_days": len(active_trade_days),
        "total_calendar_days": total_calendar_days,
        "avg_hours_between_signals": (
            f"{avg_hours_between_signals_value:.2f} hours"
            if avg_hours_between_signals_value is not None
            else "N/A"
        ),
        "avg_hours_between_signals_value": (
            round(avg_hours_between_signals_value, 4)
            if avg_hours_between_signals_value is not None
            else None
        ),
        "longest_quiet_gap": f"{longest_quiet_gap_days_value:.2f} days",
        "longest_quiet_gap_days": round(longest_quiet_gap_days_value, 4),
        "quiet_gap_status": quiet_gap_status,
        "sample_days": round(period_days, 2),
        "sample_confidence": sample_confidence,
        "explanation": (
            f"This setup behaved like {trade_style.lower()} over the tested sample, "
            f"with {signals_per_day_value:.2f} signals per day and a longest quiet gap of "
            f"{longest_quiet_gap_days_value:.2f} days."
        ),
    }


def get_current_signal_summary(strategy_type, df, settings, strategy=None):
    last_index = len(df) - 1
    signal = get_signal(strategy_type, df, last_index, settings, strategy=strategy)
    row = df.iloc[last_index]

    if strategy_type == "tdi_signal_reversal":
        tdi_state = get_tdi_sharkfin_state(df, last_index)

        if tdi_state["white_buy"]:
            status = "LONG"
            action = "TDI WHITE BUY SIGNAL ACTIVE"
            message = (
                "Original TDI white BUY label detected: "
                "fastMA curled upward below 32. The spot agent should buy the selected token if not already holding it."
            )
        elif tdi_state["white_sell"]:
            status = "SHORT"
            action = "TDI WHITE SELL SIGNAL ACTIVE"
            message = (
                "Original TDI white SELL label detected: "
                "fastMA curled downward above 68. The spot agent should sell/reduce the selected token only if it already holds it."
            )
        else:
            status = "HOLD"
            action = "NO ACTIVE TDI WHITE SIGNAL"
            message = (
                "No original TDI white BUY or SELL label on the latest closed candle. "
                "Turquoise crosses and signal-line exits are ignored."
            )

        return {
            "status": status,
            "action": action,
            "latest_close": round(row["close"], 4),
            "latest_rsi": round(row["rsi"], 2),
            "latest_deviation": round(row["deviation"], 2),
            "tdi": tdi_state,
            "message": message,
        }

    if strategy_type == "tdi_bottom_to_top_reversal":
        tdi_state = get_tdi_bottom_to_top_state(df, last_index, strategy=strategy)

        if tdi_state["long_entry"]:
            status = "LONG"
            action = "IKQF TDI BOTTOM-TO-TOP BUY SIGNAL ACTIVE"
            message = (
                f"Bottom-to-Top entry confirmed with {tdi_state['confidence_score']}/100 confidence: "
                "lower-zone reversal, trend filter, and volume/structure confirmation all passed."
            )
        elif tdi_state["short_exit"]:
            status = "SHORT"
            action = "IKQF TDI BOTTOM-TO-TOP EXIT SIGNAL ACTIVE"
            message = (
                "Bottom-to-Top reduce-risk/exit condition is active. "
                "The spot agent will only sell if the wallet already holds the selected asset."
            )
        else:
            status = "HOLD"
            action = "NO ACTIVE IKQF TDI BOTTOM-TO-TOP SIGNAL"
            failed = [name for name, passed in tdi_state["entry_checks"].items() if not passed]
            message = (
                f"No Bottom-to-Top entry on the latest candle. Confidence: {tdi_state['confidence_score']}/100. "
                f"Failed entry checks: {', '.join(failed) if failed else 'none'}."
            )

        return {
            "status": status,
            "action": action,
            "latest_close": round(row["close"], 4),
            "latest_rsi": round(row["rsi"], 2),
            "latest_deviation": round(row["deviation"], 2),
            "tdi": tdi_state,
            "message": message,
        }

    if signal:
        return {
            "status": signal.upper(),
            "action": f"{signal.upper()} SIGNAL ACTIVE",
            "latest_close": round(row["close"], 4),
            "latest_rsi": round(row["rsi"], 2),
            "latest_deviation": round(row["deviation"], 2),
            "message": f"{signal.upper()} setup detected on latest closed candle."
        }

    return {
        "status": "HOLD",
        "action": "NO ACTIVE ENTRY",
        "latest_close": round(row["close"], 4),
        "latest_rsi": round(row["rsi"], 2),
        "latest_deviation": round(row["deviation"], 2),
        "message": "No valid entry signal on latest closed candle."
    }

def run_backtest(
    strategy,
    coin,
    timeframe,
    risk,
    initial_capital=10000
):
    symbol = normalize_symbol(coin)
    interval = timeframe_to_binance(timeframe)
    settings = get_risk_settings(risk)
    strategy_type = strategy.get("type", "")
    total_cost_pct = settings["fee_per_trade"] + settings["slippage_per_trade"]

    df = fetch_binance_klines(
        symbol=symbol,
        interval=interval,
        limit=get_backtest_limit(timeframe)
    )

    df = build_indicators(df)

    midpoint = len(df) // 2

    first_half_return = (
        (df["close"].iloc[midpoint] - df["close"].iloc[0])
        / df["close"].iloc[0]
    ) * 100

    second_half_return = (
        (df["close"].iloc[-1] - df["close"].iloc[midpoint])
        / df["close"].iloc[midpoint]
    ) * 100

    consistency_pass = (
        first_half_return > 0 and
        second_half_return > 0
    )

    current_signal = get_current_signal_summary(
        strategy_type,
        df,
        settings,
        strategy=strategy,
    )

    buy_hold_return = (
        (df["close"].iloc[-1] - df["close"].iloc[0])
        / df["close"].iloc[0]
    ) * 100

    in_trade = False
    trade_dir = None
    entry_price = None
    entry_time = None
    entry_dev = None
    entry_index = None
    peak_price = None

    trades = []
    equity = initial_capital
    peak_equity = equity
    max_drawdown = 0
    max_drawdown_initial_capital = 0
    equity_curve = [equity]
    equity_curve_points = [
        {
            "trade": 0,
            "equity": round(equity, 2),
            "date": df["open_time"].iloc[0].strftime("%Y-%m-%d %H:%M"),
            "timestamp": df["open_time"].iloc[0].isoformat(),
        }
    ]
    buy_hold_curve = [initial_capital]

    for index in range(2, len(df)):
        row = df.iloc[index]
        close = row["close"]

        if not in_trade:
            signal = get_signal(strategy_type, df, index, settings, strategy=strategy)

            # Bottom-to-Top is spot-only. Its "short" signal is an exit/reduce
            # instruction and must never open a synthetic short in the backtest.
            if strategy_type == "tdi_bottom_to_top_reversal" and signal == "short":
                signal = None

            if signal:
                in_trade = True
                trade_dir = signal
                entry_price = close
                entry_time = row["open_time"]
                entry_dev = row["deviation"]
                entry_index = index
                peak_price = close

        else:
            peak_price = max(float(peak_price or close), float(close))
            exit_reason = None
            raw_pnl_pct = None

            if strategy_type == "mean_reversion":
                win = row["deviation"] <= settings["take_profit_level"]
                loss = row["deviation"] >= entry_dev + settings["stop_extension"]

            elif strategy_type == "tdi_signal_reversal":
                # Original Pine white-label sharkfin stats use TP 1.0% and SL 0.5%.
                tdi_take_profit_pct = 1.0
                tdi_stop_loss_pct = 0.5
                win = False
                loss = False

                if trade_dir == "long":
                    win = close >= entry_price * (1 + tdi_take_profit_pct / 100)
                    loss = close <= entry_price * (1 - tdi_stop_loss_pct / 100)

                    if win:
                        exit_reason = "tdi_white_signal_take_profit"
                        raw_pnl_pct = ((close - entry_price) / entry_price) * 100
                    elif loss:
                        exit_reason = "tdi_white_signal_stop_loss"
                        raw_pnl_pct = ((close - entry_price) / entry_price) * 100
                else:
                    win = close <= entry_price * (1 - tdi_take_profit_pct / 100)
                    loss = close >= entry_price * (1 + tdi_stop_loss_pct / 100)

                    if win:
                        exit_reason = "tdi_white_signal_take_profit"
                        raw_pnl_pct = ((entry_price - close) / entry_price) * 100
                    elif loss:
                        exit_reason = "tdi_white_signal_stop_loss"
                        raw_pnl_pct = ((entry_price - close) / entry_price) * 100

            elif strategy_type == "tdi_bottom_to_top_reversal":
                state = get_tdi_bottom_to_top_state(df, index, strategy=strategy)
                risk_management = strategy.get("risk_management") or {}
                stop_map = risk_management.get("hard_stop_loss_pct") or {}
                risk_key = {"low": "safe", "medium": "balanced", "high": "aggressive"}.get(
                    str(risk).lower(),
                    str(risk).lower(),
                )
                hard_stop_pct = abs(float(stop_map.get(risk_key, -5.0)))

                time_stop_cfg = risk_management.get("time_stop") or {}
                time_stop_enabled = bool(time_stop_cfg.get("enabled", True))
                time_stop_minutes = float(time_stop_cfg.get("exit_if_tdi_not_above_50_after_minutes", 90))
                elapsed_minutes = max(
                    0.0,
                    (row["open_time"] - entry_time).total_seconds() / 60.0,
                )

                raw_pnl_pct = ((close - entry_price) / entry_price) * 100
                peak_pnl_pct = ((peak_price - entry_price) / entry_price) * 100

                break_even_exit = peak_pnl_pct >= 1.0 and raw_pnl_pct <= 0.0

                trailing_cfg = risk_management.get("trailing_stop") or {}
                trailing_enabled = bool(trailing_cfg.get("enabled", True))
                trailing_activate = float(trailing_cfg.get("activate_after_profit_pct", 2.0))
                trail_from_peak_pct = float(trailing_cfg.get("trail_from_peak_pct", 30))
                trailing_floor = peak_pnl_pct * (1.0 - trail_from_peak_pct / 100.0)
                trailing_exit = (
                    trailing_enabled
                    and peak_pnl_pct >= trailing_activate
                    and raw_pnl_pct <= trailing_floor
                )

                upper_exit = bool(state["upper_reached"])
                cross_down_after_profit = bool(state["cross_down"] and raw_pnl_pct > 0)
                structure_exit = bool(state["structure_lost"])
                hard_stop_exit = raw_pnl_pct <= -hard_stop_pct
                time_stop_exit = bool(
                    time_stop_enabled
                    and elapsed_minutes >= time_stop_minutes
                    and float(state["tdi_fast"]) < 50
                )
                regime_exit = bool(state["bearish_regime"])

                should_exit = any([
                    upper_exit,
                    cross_down_after_profit,
                    structure_exit,
                    hard_stop_exit,
                    time_stop_exit,
                    regime_exit,
                    break_even_exit,
                    trailing_exit,
                ])

                if should_exit:
                    win = raw_pnl_pct >= 0
                    loss = not win
                    if hard_stop_exit:
                        exit_reason = "hard_stop_loss_hit"
                    elif upper_exit:
                        exit_reason = "tdi_green_reaches_upper_zone_68"
                    elif cross_down_after_profit:
                        exit_reason = "tdi_green_crosses_down_red_after_profit"
                    elif structure_exit:
                        exit_reason = "price_loses_reversal_structure"
                    elif time_stop_exit:
                        exit_reason = "time_stop_hit"
                    elif regime_exit:
                        exit_reason = "market_regime_turns_bearish"
                    elif trailing_exit:
                        exit_reason = "trailing_stop_hit"
                    else:
                        exit_reason = "break_even_guard"
                else:
                    win = False
                    loss = False
                    raw_pnl_pct = None

            else:
                if strategy_type in ("mean_reversion_channel", "trend_confluence"):
                    win_target_pct = 1.0
                    loss_target_pct = -1.0
                else:
                    win_target_pct = settings["win_pnl"]
                    loss_target_pct = settings["loss_pnl"]

                if trade_dir == "long":
                    win = close >= entry_price * (1 + win_target_pct / 100)
                    loss = close <= entry_price * (1 + loss_target_pct / 100)
                else:
                    win = close <= entry_price * (1 - win_target_pct / 100)
                    loss = close >= entry_price * (1 - loss_target_pct / 100)

            if win or loss:
                if strategy_type in ("tdi_signal_reversal", "tdi_bottom_to_top_reversal") and raw_pnl_pct is not None:
                    raw_pnl_pct = raw_pnl_pct
                elif strategy_type in ("mean_reversion_channel", "trend_confluence"):
                    raw_pnl_pct = 1.0 if win else -1.0
                else:
                    raw_pnl_pct = settings["win_pnl"] if win else settings["loss_pnl"]

                pnl_pct = raw_pnl_pct - total_cost_pct
                bars_in_trade = index - entry_index

                equity = equity * (1 + pnl_pct / 100)
                equity_curve.append(equity)
                equity_curve_points.append({
                    "trade": len(equity_curve) - 1,
                    "equity": round(equity, 2),
                    "date": row["open_time"].strftime("%Y-%m-%d %H:%M"),
                    "timestamp": row["open_time"].isoformat(),
                })
                peak_equity = max(peak_equity, equity)

                buy_hold_equity = initial_capital * (close / df["close"].iloc[0])
                buy_hold_curve.append(round(buy_hold_equity, 2))

                drawdown = ((peak_equity - equity) / peak_equity) * 100
                max_drawdown = max(max_drawdown, drawdown)

                drawdown_initial = ((peak_equity - equity) / initial_capital) * 100
                max_drawdown_initial_capital = max(max_drawdown_initial_capital, drawdown_initial)

                if strategy_type in ("tdi_signal_reversal", "tdi_bottom_to_top_reversal"):
                    recorded_exit_reason = exit_reason
                else:
                    recorded_exit_reason = "take_profit" if win else "stop_loss"

                trades.append({
                    "entry_time": entry_time.strftime("%Y-%m-%d %H:%M"),
                    "entry_timestamp": entry_time.isoformat(),
                    "exit_time": row["open_time"].strftime("%Y-%m-%d %H:%M"),
                    "exit_timestamp": row["open_time"].isoformat(),
                    "side": trade_dir,
                    "entry_price": round(entry_price, 4),
                    "exit_price": round(close, 4),
                    "result": "win" if win else "loss",
                    "pnl_pct": round(pnl_pct, 2),
                    "raw_pnl_pct": round(raw_pnl_pct, 2),
                    "fee_pct": settings["fee_per_trade"],
                    "slippage_pct": settings["slippage_per_trade"],
                    "total_cost_pct": round(total_cost_pct, 2),
                    "bars_in_trade": bars_in_trade,
                    "exit_reason": recorded_exit_reason,
                    "duration": f"{bars_in_trade} bars",
                })

                in_trade = False
                trade_dir = None
                entry_price = None
                entry_time = None
                entry_dev = None
                entry_index = None
                peak_price = None

    wins = len([t for t in trades if t["result"] == "win"])
    losses = len([t for t in trades if t["result"] == "loss"])
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0

    trade_returns = [t["pnl_pct"] for t in trades]

    gross_profit = sum(t["pnl_pct"] for t in trades if t["result"] == "win")
    gross_loss = abs(sum(t["pnl_pct"] for t in trades if t["result"] == "loss"))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit

    net_return = ((equity - initial_capital) / initial_capital) * 100
    strategy_vs_buy_hold = net_return - buy_hold_return
    risk_adjusted_score = net_return - max_drawdown

    drawdown_gate = "PASS" if max_drawdown <= DRAWDOWN_LIMIT else "FAIL"
    min_trade_gate = "PASS" if total >= MIN_TRADES_REQUIRED else "FAIL"

    winning_returns = [t["pnl_pct"] for t in trades if t["result"] == "win"]
    losing_returns = [t["pnl_pct"] for t in trades if t["result"] == "loss"]

    avg_win = sum(winning_returns) / len(winning_returns) if winning_returns else 0
    avg_loss = sum(losing_returns) / len(losing_returns) if losing_returns else 0
    payoff_ratio = avg_win / abs(avg_loss) if avg_loss != 0 else avg_win
    avg_pnl = sum(t["pnl_pct"] for t in trades) / total if total > 0 else 0
    largest_profit = max([t["pnl_pct"] for t in trades], default=0)
    largest_loss = min([t["pnl_pct"] for t in trades], default=0)
    avg_bars_in_trade = sum(t["bars_in_trade"] for t in trades) / total if total > 0 else 0
    avg_drawdown_duration = calculate_drawdown_durations(equity_curve)

    sharpe_ratio = calculate_sharpe_ratio(trade_returns)
    sortino_ratio = calculate_sortino_ratio(trade_returns)
    calmar_ratio = net_return / max_drawdown if max_drawdown > 0 else 0
    expectancy = avg_pnl

    sharpe_ratio = calculate_sharpe_ratio(trade_returns)
    sortino_ratio = calculate_sortino_ratio(trade_returns)
    calmar_ratio = net_return / max_drawdown if max_drawdown > 0 else 0
    expectancy = avg_pnl
    recovery_factor = net_return / max_drawdown if max_drawdown > 0 else net_return

    max_win_streak = 0
    max_loss_streak = 0

    current_win_streak = 0
    current_loss_streak = 0

    for trade in trades:
        if trade["result"] == "win":
            current_win_streak += 1
            current_loss_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)

        else:
            current_loss_streak += 1
            current_win_streak = 0
            max_loss_streak = max(max_loss_streak, current_loss_streak)

    activity_profile = calculate_activity_profile(
        trades=trades,
        backtest_start=df["open_time"].iloc[0],
        backtest_end=df["open_time"].iloc[-1],
    )

    return {
        "mode": "real_binance_backtest",
        "symbol": symbol,
        "timeframe": interval,
        "strategy_type": strategy_type,
        "activity_profile": activity_profile,
        "activity_status": activity_profile["activity_status"],
        "trade_style": activity_profile["trade_style"],
        "signals_per_day": activity_profile["signals_per_day"],
        "signals_per_day_value": activity_profile["signals_per_day_value"],
        "active_days_pct": activity_profile["active_days_pct"],
        "active_days_pct_value": activity_profile["active_days_pct_value"],
        "avg_hours_between_signals": activity_profile["avg_hours_between_signals"],
        "longest_quiet_gap": activity_profile["longest_quiet_gap"],
        "longest_quiet_gap_days": activity_profile["longest_quiet_gap_days"],
        "quiet_gap_status": activity_profile["quiet_gap_status"],
        "sample_confidence": activity_profile["sample_confidence"],
        "risk_model": risk.lower(),
        "settings_used": settings,
        "transaction_cost_per_trade": f"{settings['fee_per_trade']:.2f}%",
        "slippage_per_trade": f"{settings['slippage_per_trade']:.2f}%",
        "total_cost_per_trade": f"{total_cost_pct:.2f}%",
        "drawdown_limit": f"{DRAWDOWN_LIMIT:.2f}%",
        "drawdown_gate": drawdown_gate,
        "min_trades_required": MIN_TRADES_REQUIRED,
        "min_trade_gate": min_trade_gate,
        "candles_tested": len(df),
        "backtest_start": df["open_time"].iloc[0].strftime("%Y-%m-%d"),
        "backtest_end": df["open_time"].iloc[-1].strftime("%Y-%m-%d"),
        "backtest_period": f"{df['open_time'].iloc[0].strftime('%Y-%m-%d')} to {df['open_time'].iloc[-1].strftime('%Y-%m-%d')}",
        "trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": f"{win_rate:.2f}%",
        "net_return": f"{net_return:.2f}%",
        "current_signal": current_signal,
        "first_half_return": f"{first_half_return:.2f}%",
        "second_half_return": f"{second_half_return:.2f}%",
        "consistency_gate": "PASS" if consistency_pass else "FAIL",
        "buy_hold_return": f"{buy_hold_return:.2f}%",
        "strategy_vs_buy_hold": f"{strategy_vs_buy_hold:.2f}%",
        "max_drawdown": f"{max_drawdown:.2f}%",
        "max_drawdown_initial_capital": f"{max_drawdown_initial_capital:.2f}%",
        "avg_drawdown_duration": f"{avg_drawdown_duration:.2f} trades",
        "avg_pnl": f"{avg_pnl:.2f}%",
        "avg_win": f"{avg_win:.2f}%",
        "avg_loss": f"{avg_loss:.2f}%",
        "payoff_ratio": round(payoff_ratio, 2),
        "largest_profit": f"{largest_profit:.2f}%",
        "largest_loss": f"{largest_loss:.2f}%",
        "avg_bars_in_trade": f"{avg_bars_in_trade:.2f}",
        "expectancy": f"{expectancy:.2f}%",
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "sharpe_ratio": round(sharpe_ratio, 2),
        "sortino_ratio": round(sortino_ratio, 2),
        "calmar_ratio": round(calmar_ratio, 2),
        "recovery_factor": round(recovery_factor, 2),
        "profit_factor": round(profit_factor, 2),
        "risk_adjusted_score": round(risk_adjusted_score, 2),
        "initial_capital": f"${initial_capital:,.2f}",
        "final_equity": f"${equity:,.2f}",
        "equity_curve": [round(x, 2) for x in equity_curve],
        "equity_curve_points": equity_curve_points,
        "buy_hold_curve": buy_hold_curve,
        "recent_trades": trades[-20:]
    }