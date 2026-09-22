# IKQF fixed deployable package

This package reconciles the September backend/frontend with the previously missing IKQF v2 engine modules.

## What was fixed

- Restored the six IKQF v2 engine modules: opportunity_engine, market_scanner, coin_ranker, regime_detector, confidence_engine, capital_allocator.
- V2 market scanner now considers only tokens accepted by the live trade-safety allowlist.
- TWAK portfolio no longer tries to use an arbitrary `--address` argument. It reads the local signing wallet and verifies it against the configured address.
- Live trading fails closed unless `AGENT_WALLET_ADDRESS` (or `TWAK_AGENT_ADDRESS`) is explicitly set and matches the local TWAK signing wallet.
- STOP trips a live-execution kill switch. The kill switch is checked again immediately before live TWAK swaps.
- Direct `/execute-trade` also respects the kill switch and wallet identity verification.
- Simulation/paper mode no longer requires a live wallet baseline just to start.
- Wallet baseline, saved agent setup, trade log and live-trade cooldown state can persist under `IKQF_STATE_DIR`.
- Trade cooldown survives process restarts.
- Production HTTP CORS origins were removed; HTTPS production origins remain.
- Debug endpoints now require the operator key.
- Binance-US fallback was removed from candle data to avoid silently mixing markets.
- Legacy `binance_data.py` now supports 1M and rejects unsupported timeframes rather than silently defaulting to 4H.
- Backend Node dependencies are pinned instead of using `latest`.
- Frontend no longer claims PancakeSwap is always the routing venue; TWAK may choose the route.
- Frontend TWAK status starts as UNKNOWN rather than falsely CONFIGURED/READY.

## Strategy files

`backend/strategies/` contains the seven strategy types actually implemented by the current `backtest.py`.

The newer strategy-pack JSONs are preserved in `backend/strategies_experimental/` but are deliberately not loaded into live AUTO trading. Their JSON documents require extra execution/data logic (market breadth, spread/liquidity, news, grid order lifecycle, rotation state, etc.) that the present backend does not implement. Loading them as if executable would be unsafe and misleading.

## Railway persistence

Mount a Railway Volume at `/data`.

Use:

- `IKQF_HOME=/data`
- `IKQF_STATE_DIR=/data/ikqf_state`

The TWAK wallet will then live below `/data/.twak` and IKQF state below `/data/ikqf_state`.

Do **not** automatically create a replacement production wallet after a redeploy. `IKQF_CREATE_WALLET_IF_MISSING` defaults to false. If you intentionally create a wallet, set the resulting BSC address as `AGENT_WALLET_ADDRESS` and confirm `/twak-status` reports `live_execution_ready: true` before live trading.

## Backend deployment

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install Node/TWAK dependencies:

```bash
npm install
```

Start:

```bash
./start.sh
```

Health endpoint:

`GET /health`

Before live trading, verify:

`GET /twak-status`

The important fields must be:

- `configured_address_is_explicit: true`
- `cli_address_matches_configured: true`
- `live_execution_ready: true`

## Frontend

Set `VITE_API_URL` to the backend URL, then:

```bash
npm ci
npm run build
```

## Test status in this package

- Python compileall: PASS
- Backend import: PASS
- Required API routes: PASS
- Mocked decision-simulation agent cycle: PASS
- Mocked IKQF v2 opportunity-engine call: PASS
- Shell syntax (`start.sh`): PASS
- Frontend source changes are limited to text/status wiring; dependency installation in this environment was too slow to complete, so the production Vite build must still be run in your normal Node/Railway build environment.

No blockchain transaction was sent during these tests.
