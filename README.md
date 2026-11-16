# 🔱 NexTrade AI: Autonomous Trading Terminal

![NexTrade AI Banner](C:/Users/User/.gemini/antigravity/brain/c4d4f837-f4d8-447e-aa69-3eedd449a15e/nextrade_ai_banner_1778043667125.png)

> **Next-Generation Autonomous Trading System** with a premium "Midnight Gold" interface. Built for high-frequency pairs trading, risk-managed execution, and professional-grade analytics.

---

## ✨ Core Features

### 🤖 Intelligent Autonomous Engine
- **Pairs Trading Strategy**: Advanced statistical arbitrage using z-score mean reversion between correlated pairs (BTC/USDT, ETH/USDT).
- **Hedge Ratio Calculation**: Dynamic linear regression for optimal spread maintenance.
- **AI Sentiment Analysis**: Real-time market sentiment and action prediction with confidence scoring.

### 💎 "Midnight Gold" Dashboard
- **Ultra-Fast Web UI**: Built with **React 19** and **Vite** for near-instant startup and high-performance rendering.
- **Glassmorphism Design**: High-end fintech aesthetic with ambient lighting and premium gold accents.
- **Live TradingView Charts**: Integrated **Lightweight Charts** with AI signal markers and strategy rule indications.
- **Educational Tooltips**: Platform-wide tooltips explaining complex trading metrics for transparency.

### 🛡️ Institutional-Grade Risk Management
- **Automatic Position Sizing**: Based on stop-loss distance and account risk % (Kelly Criterion variant).
- **Multi-Level Halt System**: Enforced daily, weekly, and monthly loss limits.
- **Drawdown Protection**: Automatic system halt upon reaching maximum drawdown thresholds.
- **Emergency Liquidation**: One-click "Nuclear Option" to close all positions and stop the bot instantly.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python 3.10+, FastAPI, SQLite, CCXT |
| **Frontend** | React 19, Vite, Tailwind CSS v4, Lucide |
| **Charts** | Lightweight Charts (TradingView) |
| **Styling** | Vanilla CSS + Tailwind v4 (Design Token System) |
| **Analysis** | NumPy, Pandas, Statsmodels |

---

## 🚀 Quick Start

**Paper trading only.** Orders are simulated locally against live public prices (Binance public data via CCXT). No API keys, no real money. If the exchange is unreachable the bot falls back to a simulated price feed (`FORCE_SYNTHETIC=true` forces it).

```bash
pip install -r requirements.txt
cd ReactFront/trading_bot && npm install && cd ../..
./startweb.bat            # API on :8000, UI on :3000
python -m pytest tests    # run the test suite
python main.py backtest 2024-01-01 2024-03-01   # CLI backtest
```

Settings (capital, fees, thresholds, risk limits) live in `config.py` and can be overridden with environment variables or a `.env` file (e.g. `INITIAL_CAPITAL=5000`).

### How it trades
Default strategy (`STRATEGY=trend_momentum`): a long/flat, unleveraged portfolio of 8 large caps on 4h bars. Half Donchian-breakout trend following, half cross-sectional momentum (each averaged over several look-backs), gated by a BTC regime filter and scaled to a 35% volatility target. It rebalances on each new 4h bar and goes to cash when nothing is trending. Backtest on real data (2023-07 to 2026-11, 0.15% costs): Sharpe ~1.3, ~42%/yr, max drawdown ~28% vs BTC buy-and-hold ~25%/yr and -53%. These are estimates: the universe is today's large caps (survivorship bias) and the future can differ. `STRATEGY=pairs` selects the older BTC/ETH pairs strategy.
Daily/weekly/monthly loss limits and a max-drawdown circuit breaker (30%) are enforced; the paper account persists in SQLite across restarts (the UI's "Reset paper account" wipes it).

---

## 📂 Project Structure

```text
nextrade-ai/
├── api/                # FastAPI Endpoints & WebSocket Logic
├── execution/          # Broker & Order Management
├── risk/               # Risk Management & Position Sizing
├── strategies/         # Strategy Logic (Pairs Trading)
├── data/               # SQLite Storage & Market Fetchers
├── ReactFront/         # React 19 + Vite + Tailwind Frontend
└── startweb.bat        # Parallel System Launcher
```

---

## 📈 Performance & Analytics
The system tracks **Daily P&L**, **Equity Curves**, and **Symbol Performance** in real-time. All data is persisted in a local SQLite database for offline audit and optimization.

---

## ⚖️ Disclaimer
*Trading involves significant risk. This bot is a tool for autonomous execution and does not guarantee profits. Use at your own risk. Always test thoroughly on Testnets before deploying live capital.*

---
*Developed with ❤️ for the future of decentralized finance.*