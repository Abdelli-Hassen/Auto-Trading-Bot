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

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **Git**

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/nextrade-ai.git
cd nextrade-ai

# Setup Backend
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Setup Frontend
cd ReactFront/trading_bot
npm install
```

### 3. Configuration
Rename `config.py.example` (if provided) or edit `config.py`:
- Set `TESTNET = True` for initial testing.
- Add your Exchange API Keys.
- Adjust `INITIAL_CAPITAL` and risk parameters.

### 4. Launch
Use the parallel launcher to start the entire system in one click:
```bash
./startweb.bat
```
*This will launch the FastAPI server, the Tailwind watcher, and the Vite dev server simultaneously.*

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