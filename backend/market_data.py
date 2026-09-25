import requests
import pandas as pd


BINANCE_KLINE_ENDPOINTS = [
    # Official market-data-only host. Use this first because Railway/cloud IPs can
    # receive HTTP 451 from the general Binance API hosts even for public candles.
    "https://data-api.binance.vision/api/v3/klines",
    "https://api-gcp.binance.com/api/v3/klines",
    "https://api.binance.com/api/v3/klines",
    "https://api1.binance.com/api/v3/klines",
    "https://api2.binance.com/api/v3/klines",
    "https://api3.binance.com/api/v3/klines",
    "https://api4.binance.com/api/v3/klines",
]


def fetch_binance_klines(symbol: str, interval: str = "4h", limit: int = 500):
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit,
    }

    last_error = None
    data = None
    used_url = None

    for url in BINANCE_KLINE_ENDPOINTS:
        try:
            response = requests.get(url, params=params, timeout=12)
            response.raise_for_status()
            data = response.json()
            used_url = url
            break
        except Exception as error:
            last_error = error

    if data is None:
        raise RuntimeError(
            f"Binance kline lookup failed for {params['symbol']} {interval}: {last_error}"
        )

    if not isinstance(data, list) or len(data) == 0:
        raise RuntimeError(
            f"Binance kline lookup returned no candles for {params['symbol']} {interval} from {used_url}."
        )

    df = pd.DataFrame(data, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_volume", "taker_buy_quote_volume", "ignore",
    ])

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

    # Binance includes the currently forming candle in /klines. Trading decisions
    # must use confirmed candles only; otherwise a 5M sharkfin on the candle that
    # just closed can be missed because the next unfinished candle becomes df[-1].
    now_utc = pd.Timestamp.now(tz="UTC").tz_localize(None)
    df = df[df["close_time"] <= now_utc].copy()

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_asset_volume",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=["open", "high", "low", "close", "volume"])

    if df.empty:
        raise RuntimeError(
            f"Binance kline lookup produced no valid CLOSED numeric candles for {params['symbol']} {interval}."
        )

    # Preserve source diagnostics without changing the existing dataframe API.
    df.attrs["source_url"] = used_url
    df.attrs["closed_candles_only"] = True
    return df.reset_index(drop=True)
