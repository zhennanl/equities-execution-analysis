# Execution Analytics Platform

An agentic multi-module platform for equity execution analysis, built with Python and Streamlit.

## Modules

### 1. Execution Algorithm Simulator
A multi-agent pipeline that analyses live market data and compares execution algorithms (VWAP, TWAP, Implementation Shortfall, POV) across market regimes.

**Agent pipeline:**
- **Agent 1 — Market Data**: Fetches intraday OHLCV data, computes ADV and realised volatility
- **Agent 2 — Market Regime** *(coming soon)*: Classifies volatility and volume regime
- **Agent 3 — Algorithm Simulation** *(coming soon)*: Simulates VWAP, TWAP, IS, POV on synthetic orders
- **Agent 4 — Performance Comparison** *(coming soon)*: Compares execution cost in bps across algorithms
- **Agent 5 — LLM Recommendation** *(coming soon)*: Generates natural language execution recommendation memo

**Supported markets:** Taiwan (TWSE), Hong Kong (HKEX), Japan (TSE), Korea (KRX), US

### 2. Index Rebalancing Analysis *(coming soon)*
Event study analysis of stock price and volume dynamics around index rebalancing events, with market impact estimation.

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tech Stack
- **Data**: yfinance (live market data, no API key required)
- **UI**: Streamlit
- **Charts**: Plotly
- **Agents**: Claude Agent SDK
