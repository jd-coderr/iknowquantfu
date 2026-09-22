#!/usr/bin/env bash
set -euo pipefail

export HOME="${IKQF_HOME:-/data}"
export IKQF_STATE_DIR="${IKQF_STATE_DIR:-/data/ikqf_state}"
mkdir -p "$HOME/.twak" "$IKQF_STATE_DIR"

npm install --omit=dev

if [ ! -f "$HOME/.twak/wallet.json" ]; then
  if [ "${IKQF_CREATE_WALLET_IF_MISSING:-false}" = "true" ]; then
    : "${TWAK_WALLET_PASSWORD:?TWAK_WALLET_PASSWORD is required to create a TWAK wallet}"
    npx @trustwallet/cli wallet create --password "$TWAK_WALLET_PASSWORD" --no-keychain --skip-password-check --json
    echo "Created a new TWAK wallet. IKQF will auto-detect its BSC signing address; AGENT_WALLET_ADDRESS is optional and acts as a mismatch guard."
  else
    echo "No TWAK wallet found at $HOME/.twak/wallet.json. Backend will start, but live trading remains blocked."
  fi
fi

if [ -f "$HOME/.twak/wallet.json" ] && [ -n "${TWAK_WALLET_PASSWORD:-}" ]; then
  npx @trustwallet/cli wallet status --json || true
  npx @trustwallet/cli wallet address --chain bsc --password "$TWAK_WALLET_PASSWORD" --json || true
fi

exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}"
