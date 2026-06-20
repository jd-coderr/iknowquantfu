# I Know Quant Fu

https://www.iknowquantfu.com

https://www.youtube.com/watch?v=LBmOMBLQiYQ

## Autonomous Crypto Trading Agent for the BNB Hack: AI Trading Agent Edition

**I Know Quant Fu** is an autonomous crypto trading agent built for the **BNB Hack: AI Trading Agent Edition — CoinMarketCap × Trust Wallet** competition.

It connects CoinMarketCap market intelligence, CoinMarketCap x402 paid data, strategy testing, risk control, and Trust Wallet Agent Kit execution into one explainable trading loop.

**Roundhouse kick dumb trades.**
**Backtest the signal. Lock the risk. Automate the move.**

The agent does not chase candles.

It reads the market, tests the strategy, checks the risk, explains the decision, and only then decides whether to wait, simulate, paper trade, or execute.

No confidence. No trade.
No logic. No trade.
No dojo. No roundhouse.

---

## Live Project

Website:

```txt
https://www.iknowquantfu.com
```

Backend:

```txt
https://strategy-forge-production-a3f6.up.railway.app
```

The backend URL may still contain the old project name because it is the Railway service URL, not the visible product branding.

---

## Vision

I Know Quant Fu bridges market intelligence and disciplined execution.

It reads CoinMarketCap signals, uses CoinMarketCap x402 paid market data, compares and backtests strategies, applies risk guardrails, then decides whether to wait, simulate, paper trade, or execute through Trust Wallet Agent Kit on BNB Chain with on-chain proof.

The goal is not just automation.

The goal is explainable, self-custodial, risk-aware trading.

---

## Problem

Crypto traders often face two bad options:

1. **Manual trading**, where emotion, fear, greed, and inconsistent rules lead to bad entries and poor risk control.

2. **Basic trading bots**, which blindly execute fixed rules without understanding market regime, confidence, risk, or whether a trade should be skipped.

Most systems also separate the market intelligence layer from the wallet execution layer.

A user reads data in one place, makes decisions somewhere else, and manually executes trades through another interface.

I Know Quant Fu solves this by connecting the full loop:

```txt
CoinMarketCap intelligence
→ CoinMarketCap x402 paid market data
→ strategy comparison
→ backtesting
→ confidence scoring
→ risk guardrails
→ autonomous decision
→ TWAK execution
→ BNB Chain proof
```

---

## What It Does

I Know Quant Fu can:

* Read CoinMarketCap market intelligence
* Pay for CoinMarketCap market data through x402 using Base USDC
* Verify successful x402 payment responses
* Use paid CoinMarketCap quote data inside the agent decision loop
* Detect market regime and sentiment conditions
* Generate, compare, and backtest trading strategies
* Rank strategies by risk-adjusted performance
* Apply confidence scoring and drawdown protection
* Decide whether to hold, simulate, paper trade, or execute live
* Connect to a user wallet
* Read live portfolio state through Trust Wallet Agent Kit
* Attempt execution through Trust Wallet Agent Kit
* Route swaps through PancakeSwap on BNB Smart Chain
* Display trade decisions, execution status, portfolio state, and proof
* Maintain paper trading history and performance analytics
* Explain why it acted — or why it waited

Waiting is not a bug.

Waiting is the agent refusing to roundhouse kick itself in the face.

---

## Core Agent Loop

```txt
Market Data In
→ CoinMarketCap x402 Paid Quote
→ Strategy Engine
→ Backtest + Optimizer
→ Confidence Model
→ Risk Governor
→ Decision Engine
→ TWAK / Wallet Execution
→ On-Chain Proof
```

The agent does not force trades.

If the market is unclear, confidence is too low, or risk controls fail, the agent can choose:

```txt
HOLD / NO EXECUTION
```

This is intentional.

The agent is designed to avoid dumb trades, not chase every signal.

---

## Competition Track

This project is built for:

```txt
Track 1: Autonomous Trading Agents
BNB Hack: AI Trading Agent Edition
CoinMarketCap × Trust Wallet
```

The project focuses on:

* Autonomous trading logic
* CoinMarketCap-powered market intelligence
* CoinMarketCap x402 paid data
* Trust Wallet Agent Kit execution
* Self-custody wallet flow
* BNB Chain settlement
* Risk-aware trading guardrails
* On-chain proof of execution

---

## Registered Agent Wallet

The agent wallet used for the competition is:

```txt
0x695b32DdB023f76dE3FE4de485F7C0131De4754C
```

BSC explorer:

```txt
https://bscscan.com/address/0x695b32DdB023f76dE3FE4de485F7C0131De4754C
```

Registration status reported by the application:

```txt
registered: true
alreadyRegistered: true
chain: bsc
```

Registration proof status:

```txt
Application reports the agent wallet as registered on BSC.
Exact competition registration transaction hash should be added if required by judges.
```

---

## Agent Wallet Funding Proof

The agent wallet has been funded on BNB Smart Chain and holds non-zero in-scope assets.

Funding transaction:

```txt
0x4f5469a769c9298572fee10da3fbc92b9db57f032d262ffe283e4882537ac9f
```

Funding transaction link:

```txt
https://bscscan.com/tx/0x4f5469a769c9298572fee10da3fbc92b9db57f032d262ffe283e4882537ac9f
```

This transaction proves that the agent wallet received BNB for gas.

It is **wallet funding proof**, not a live trade proof.

---

## Current On-Chain Wallet State

The agent wallet currently shows non-zero balances on BNB Smart Chain, including:

```txt
BNB
Binance-Peg ETH
Binance-Peg USDT
```

This matters because Track 1 requires the agent wallet to hold non-zero in-scope assets at competition start and maintain capital for the live trading window.

Verified portfolio read through Trust Wallet Agent Kit:

```txt
portfolio.success: true
chain: bsc
agent wallet: 0x695b32DdB023f76dE3FE4de485F7C0131De4754C
```

---

## CoinMarketCap x402 Payment Proof

I Know Quant Fu includes a working CoinMarketCap x402 paid market-data flow.

The deployed backend successfully pays CoinMarketCap through x402 using Base USDC and receives live paid market data back into the agent decision loop.

Verified x402 proof:

```txt
success: true
paid: true
used_in_decision: true
provider: CoinMarketCap
protocol: x402
endpoint: https://pro-api.coinmarketcap.com/x402/v3/cryptocurrency/quotes/latest
payment_network: Base
payment_chain_id: 8453
payment_asset: USDC
asset: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
assetTransferMethod: eip3009
expected_price_usd: 0.01
http_status: 200
payment_response_header_present: true
```

x402 payment wallet:

```txt
0x209D07E2722b8BF4b9B31C8e06f0454236629cd0
```

Verified x402 payment transaction:

```txt
0x987ee0a44c51c3126fd32f529dcc96fe10e8965080d116a7a1e0fcb1eed963fc
```

Base explorer:

```txt
https://basescan.org/tx/0x987ee0a44c51c3126fd32f529dcc96fe10e8965080d116a7a1e0fcb1eed963fc
```

The paid CoinMarketCap quote was parsed by the backend and used inside the trading decision.

Verified paid ETH quote:

```txt
ETH price_usd: 1735.081898045606
```

---

## Live TWAK Execution Proof

The system is designed to detect and display BSC transaction hashes from TWAK execution output.

The agent wallet has produced real on-chain execution transactions from the registered agent wallet.

Live execution proof:

```txt
Live TWAK Execution Proof 1:
https://bscscan.com/tx/0xa6f235cead702788ea714a64247cd81064d384137a599e8b25a786635b03ffa

Live TWAK Execution Proof 2:
https://bscscan.com/tx/0xeff0d7d4ce0e021705932ea90c67bd8fb13437edf5b85427e25bf6218af31
```

Proof status:

```txt
Agent wallet funded: yes
Agent wallet has non-zero assets: yes
TWAK portfolio read path working: yes
TWAK execution path implemented: yes
Live on-chain execution proof: yes
BSC transaction hashes available: yes
CoinMarketCap x402 paid data working: yes
```

These transactions show live on-chain execution activity from the registered agent wallet on BNB Smart Chain.

They are used as execution proof. They do not claim guaranteed profit or investment performance.

---

## Verified Agent Cycle Proof

The deployed backend successfully completed a full agent cycle using paid CoinMarketCap x402 data.

Verified agent-cycle result:

```txt
success: true
mode: agent_cycle
decision: HOLD
execution_mode: simulation
portfolio.success: true
x402.success: true
x402.paid: true
x402.used_in_decision: true
x402.http_status: 200
x402.price_usd: 1735.081898045606
market_data_payment_layer: CoinMarketCap x402 paid quote
selected_strategy: FVG Channel
```

The agent chose:

```txt
HOLD
```

This was not a failure.

The agent paid for market data, checked the live wallet portfolio, selected a strategy, backtested the setup, applied risk controls, and refused execution because the current setup was not strong enough.

Verified reason:

```txt
No valid trade setup from current market conditions.
```

This demonstrates the core behavior of the project:

```txt
No confidence. No trade.
No logic. No trade.
No dumb entries.
```

---

## Features

### Market Intelligence

* CoinMarketCap market data
* CoinMarketCap Skill Hub / MCP integration
* CoinMarketCap x402 paid market-data flow
* Base USDC x402 payment support
* Paid quote verification through x402 payment response headers
* Market regime detection
* Fear and greed context
* Altcoin rotation context
* Asset and timeframe analysis

### Strategy Engine

* Strategy generation
* Multi-strategy optimization
* Historical backtesting
* Risk-adjusted ranking
* Strategy selection based on performance and guardrails

### Risk Control

* Drawdown checks
* Confidence scoring
* Risk status display
* Daily qualification guard
* Trade size controls
* Execution mode controls
* Portfolio safety checks
* Eligible-token allowlist
* Conservative per-token trade caps
* Cooldown protection between live trade attempts

### Execution Modes

The agent supports three execution modes:

```txt
Decision Simulation
Paper Trading
Live Trading
```

**Decision Simulation** logs the decision only. No live trade is executed and no virtual position is opened.

**Paper Trading** opens and closes virtual positions, tracks paper PnL, and can be reset without touching the live wallet.

**Live Trading** attempts real wallet-based execution through TWAK when configured, authorized, and allowed by the risk guardrails.

### Wallet + Execution

* Wallet connection
* BNB Smart Chain network support
* Trust Wallet Agent Kit execution layer
* PancakeSwap route support
* Transaction status display
* BSC transaction hash detection
* Agent registration display
* BscScan proof display

---

## Frontend Views

The app includes three interface modes.

### 1. Simple Version

A judge-friendly 4-panel interface that explains the project quickly and clearly.

This mode focuses on:

* What the agent is
* What it does
* When the operator uses it
* How the decision logic works

### 2. Detailed Version

A compact terminal dashboard showing agent status, strategy selection, portfolio state, execution readiness, risk controls, and system proof.

This mode is for users who want more information without reading the full trading terminal.

### 3. Full Size Version

A full scrolling terminal interface with trading controls, optimizer reports, market regime analysis, live logs, strategy analytics, backtest history, execution details, and system health.

This is the machine room.

---

## Technology Stack

### Frontend

* React
* Vite
* Recharts
* CSS terminal UI

### Backend

* Python
* FastAPI
* Railway deployment
* Node.js helper client for CoinMarketCap x402 requests

### Market Intelligence

* CoinMarketCap API
* CoinMarketCap Skill Hub MCP
* CoinMarketCap x402 paid API
* Base USDC x402 payment flow

### Wallet / Execution

* Trust Wallet Agent Kit / TWAK
* BNB Smart Chain
* PancakeSwap route logic

### Deployment

* Railway frontend
* Railway backend
* Custom domain

---

## Current Deployment

Frontend:

```txt
https://www.iknowquantfu.com
```

Backend:

```txt
https://strategy-forge-production-a3f6.up.railway.app
```

The backend URL may still contain the old project name because it is the Railway service URL, not the visible product branding.

---

## How It Works

1. The user selects an eligible asset.
2. The user chooses an execution mode.
3. The user selects trade interval and trade size.
4. The agent reads CoinMarketCap market intelligence.
5. The agent can pay CoinMarketCap through x402 for live paid quote data.
6. The agent generates or optimizes strategy logic.
7. The strategy is backtested and ranked.
8. Risk guardrails are checked.
9. The agent decides whether to wait, simulate, paper trade, or execute.
10. If execution is allowed, TWAK handles the self-custody execution path.
11. The UI displays decision, route, status, and proof.
12. If a live transaction succeeds, the UI surfaces the BSC transaction hash and BscScan proof link.

---

## Strategy Evaluation Metrics

I Know Quant Fu evaluates strategies using:

* Net return
* Win rate
* Profit factor
* Expectancy
* Sharpe ratio
* Sortino ratio
* Calmar ratio
* Recovery factor
* Maximum drawdown
* Risk-adjusted score
* Signal frequency
* Active trade days
* Quiet-gap analysis
* Strategy-vs-buy-hold comparison

---

## Example Agent Decisions

The agent may decide:

```txt
HOLD
```

when the market is neutral, risk is not clean, confidence is too low, or no valid entry signal exists.

This is not failure.

This is the agent refusing to kick a bad trade.

The agent may produce a trade plan when conditions align:

```txt
BUY / SELL
```

with route, trade size, execution status, and proof.

In live mode, successful execution should return a BSC transaction hash.

---

## Eligible Assets

The frontend and backend are designed to use competition-eligible assets only.

Examples include:

```txt
ETH
XRP
DOGE
ADA
LINK
LTC
AVAX
SHIB
DOT
UNI
AAVE
ATOM
INJ
CAKE
TWT
FIL
FET
PENDLE
FLOKI
1INCH
```

The project avoids unsupported assets where possible so competition trades stay inside the eligible-token rules.

---

## Competition Qualification Notes

For Track 1, the registered agent wallet must hold non-zero in-scope assets at the competition start.

The agent wallet currently has non-zero BNB and in-scope token balances visible on BNB Smart Chain.

The project is designed to support the competition requirement of at least one qualifying live trade per day during the trading week.

The backend includes daily live-trade counting logic designed to exclude:

```txt
Decision simulation
Paper trading
Quote-only route checks
Blocked execution attempts
```

Only real live execution results should count toward the daily qualification target.

Competition-week ranking still depends on official Track 1 rules, wallet eligibility, live trading-window activity, and real PnL measured by the competition system.

---

## Self-Custody Model

I Know Quant Fu is designed around self-custody execution.

The frontend and backend do not store seed phrases.

Signing authority should stay with the user or configured agent wallet through the Trust Wallet Agent Kit flow.

The backend generates strategy decisions, risk checks, and execution requests.

TWAK handles the wallet execution path.

The x402 payment wallet is separate from the BNB Chain agent wallet and is used to pay for CoinMarketCap x402 market-data requests.

---

## Judge Demo Flow

1. Open the live site.
2. Start in Simple Version to understand the agent.
3. Switch to Detailed Version or Full Size Version.
4. Show the registered agent wallet address.
5. Show the BSC explorer page for the agent wallet.
6. Show the wallet funding proof transaction.
7. Show the live TWAK execution proof transactions.
8. Show the CoinMarketCap x402 payment proof on Base.
9. Select an eligible asset.
10. Run auto-optimization.
11. Show selected strategy, backtest result, risk status, and confidence.
12. Run the agent.
13. Show that paid x402 market data was used in the decision.
14. Show the decision: HOLD, paper trade, or live execution.
15. If live execution succeeds, open the BscScan transaction proof.

---

## Local Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

---

## Environment Variables

Create local environment files as needed.

Do not commit real secrets.

Example frontend variable:

```env
VITE_API_URL=http://localhost:8000
```

Example backend variables may include:

```env
CMC_API_KEY=your_coinmarketcap_key
CMC_MCP_API_KEY=your_coinmarketcap_mcp_key
TWAK_CONFIG=your_twak_config
AGENT_WALLET_ADDRESS=your_agent_wallet_address
IKQF_ADMIN_KEY=your_operator_key
X402_ENABLED=true
X402_EVM_PRIVATE_KEY=your_x402_payment_wallet_private_key
```

The x402 payment wallet should be funded with enough Base USDC to pay for CoinMarketCap x402 requests.

Use `.env.example` for public documentation and keep real `.env` files private.

---

## Security Notes

Do not commit:

* Private keys
* Seed phrases
* API keys
* Wallet credentials
* Railway secrets
* Production `.env` files
* Operator admin keys

Self-custody integrity is important to the project.

Signing authority should stay with the user or configured agent wallet through the TWAK flow.

Repeated x402 tests may spend USDC, so paid endpoint testing should be limited to necessary demo and verification runs.

---

## Current Limitations

CoinMarketCap x402 paid market data is implemented and proven.

The deployed backend has successfully paid CoinMarketCap through x402 using Base USDC, received a paid quote response, parsed the ETH price, and used that paid market data inside the agent decision loop.

Trust Wallet Agent Kit portfolio access is working on Railway.

Live on-chain execution proof is available on BNB Smart Chain.

The project does not claim BNB AI Agent SDK usage unless that feature is added and proven.

Funding proof is available.

Live on-chain execution proof is available.

Competition registration status is reported by the application, but an exact registration transaction hash should be added if judges require direct registration proof.

Competition-week ranking still depends on official Track 1 rules, wallet eligibility, live trading-window activity, and real PnL measured by the competition system.

Repeated x402 tests may spend USDC, so paid endpoint testing should be limited to necessary demo and verification runs.

---

## Disclaimer

This software is provided for educational, experimental, and hackathon demonstration purposes only.

Nothing in this project is financial advice, investment advice, or a recommendation to buy or sell any asset.

Cryptocurrency trading involves significant risk and may result in loss of capital.

Past performance does not guarantee future results.

Use live trading mode only with small amounts and at your own risk.
