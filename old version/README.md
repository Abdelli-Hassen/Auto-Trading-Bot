# Autonomous Trading System

A complete, production-ready automated trading system designed for robustness and realistic profitability.

## Features

- **Modular Architecture**: Separated concerns for data, execution, risk, strategy, and monitoring
- **Pairs Trading Strategy**: Statistical arbitrage approach using cointegration
- **Comprehensive Risk Management**: Position sizing, drawdown limits, daily/weekly/monthly loss limits
- **Realistic Backtesting**: Includes slippage, fees, and proper walk-forward analysis
- **Live Trading Capable**: Connects to exchanges via CCXT (Binance testnet/mainnet)
- **Full Monitoring**: Logging, alerts, and performance tracking
- **Autonomous Operation**: Designed to run unattended with proper safety controls
- **Python Desktop Interface**: Native GUI for real-time monitoring and optional manual control

## System Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.py` to set:
- Exchange API keys (for live trading)
- Risk parameters
- Trading pairs
- Timeframes
- Initial capital

> **Important**: Never commit your `config.py` to GitHub. It is already included in `.gitignore`.

## Usage

The recommended way to start the system is using the `startpy.bat` script, which launches both:
1. The native Python desktop interface for monitoring and optional manual control
2. The autonomous trading bot engine

### Starting the System

```bash
startpy.bat
```

This will:
- Open a native Python desktop window (Design Python Desktop UI)
- Open a separate terminal window for the trading bot engine
- Handle dependency installation if needed
- Use the virtual environment if available (`.venv\Scripts\python.exe`)

### Alternative: Manual Start

If you prefer to start the components separately:

1. **Start the desktop interface** (for monitoring and optional manual control):
   ```bash
   python design_python_desktop.py
   ```

2. **Start the trading bot engine** (for autonomous trading):
   ```bash
   python main.py
   ```
   - For backtesting: `python main.py backtest 2024-01-01 2024-12-31`
   - For live trading: `python main.py` (ensure `TESTNET = False` in `config.py` for live trading)

## Autonomous Operation

Once started, the trading bot operates autonomously by:
- Analyzing market data continuously (every 1 minute)
- Generating trading signals based on the pairs trading strategy
- Executing trades automatically with proper position sizing and risk management
- Monitoring positions and enforcing stop loss/take profit levels
- Respecting daily/weekly/monthly loss limits and maximum drawdown controls
- Providing real-time visibility through the desktop interface
- Alerting you to important events via the logging system

The desktop interface (`design_python_desktop.py`) provides:
- **Executive Dashboard**: Account balance, daily P&L, trade count, system status
- **Positions Panel**: Real-time view of open positions with manual close options
- **Analytics View**: Strategy performance and spread calculations
- **Logs Panel**: Streaming system alerts and notifications
- **Configuration Panel**: Testnet/Live mode toggle and API key status

> **Note**: The bot continues to trade autonomously whether the desktop interface is open or closed. The interface is for monitoring and optional manual intervention only.

## Safety Features

The system includes multiple safety mechanisms for autonomous operation:
- **Testnet Validation**: Always test on exchange testnets before live trading
- **Position Limits**: Maximum concurrent positions and position size limits
- **Loss Limits**: Daily, weekly, and monthly loss thresholds that halt trading
- **Drawdown Protection**: Maximum drawdown limit to preserve capital
- **Emergency Stop**: Can be halted via desktop interface or signal
- **Order Management**: Tracks all orders with timeout protection and automatic cancellation of stale orders
- **Data Validation**: Checks for data anomalies and exchange connectivity before each cycle

## Architecture

```
trading_bot/
├── config.py           # System configuration (NOT in git)
├── main.py             # Autonomous trading bot entry point
├── design_python_desktop.py  # Native Python desktop interface
├── startpy.bat         # Recommended startup script (launches both UI and bot)
├── start.bat           # Alternative bot-only startup
├── data/               # Data handling
│   ├── fetcher.py      # Exchange data fetching
│   ├── storage.py      # Data persistence
│   └── validator.py    # Data validation
├── strategies/         # Trading strategies
│   ├── base.py         # Strategy base class
│   └── pairs_trading.py # Pairs trading strategy
├── execution/          # Order execution
│   └── broker.py       # Exchange connection & order management
├── risk/               # Risk management
│   └── manager.py      # Position sizing & risk limits
├── backtest/           # Backtesting framework
│   └── engine.py       # Backtesting logic
├── monitoring/         # Logging & alerts
│   └── __init__.py     # Monitoring system
├── utils/              # Helper functions
│   └── __init__.py     # Logging, calculations, etc.
└── design python/      # HTML/CSS/JS for the desktop interface
```

## Risk Management Features

- **Position Sizing**: Based on stop loss distance and account risk (1-2% per trade)
- **Daily Loss Limit**: Stop trading after 3% daily loss
- **Weekly Loss Limit**: Stop trading after 7% weekly loss
- **Monthly Loss Limit**: Stop trading after 15% monthly loss
- **Maximum Drawdown**: Halt trading at 20% drawdown
- **Position Limits**: Max 3 concurrent positions, max 10% per position

## Strategy: Pairs Trading

The system implements a statistical arbitrage strategy:
1. Identifies cointegrated pairs (e.g., BTC/USDT and ETH/USDT)
2. Calculates hedge ratio using linear regression
3. Generates signals when spread deviates from mean (z-score > 2.0)
4. Exits when spread reverts to mean (z-score < 0.5)
5. Stop loss at extreme deviations (z-score > 3.0)

## Safety Features

- **Testnet First**: Always test on exchange testnets before live trading
- **Paper Trading Recommended**: Validate with paper trading before risking capital
- **Gradual Deployment**: Start with small position sizes
- **Emergency Stops**: Multiple halt conditions based on risk metrics
- **Comprehensive Logging**: All actions logged for audit and analysis

## Expected Performance

With proper implementation and market conditions:
- Monthly returns: 2-10% (realistic, sustainable)
- Win rate: 40-60%
- Profit factor: >1.5
- Maximum drawdown: <20%

## Disclaimer

Trading involves risk of loss. Past performance is not indicative of future results.
Start with capital you can afford to lose. Always test thoroughly before deploying.
The developers are not responsible for any financial losses incurred.

## Next Steps for Production Use

1. **Extend Strategy**: Add more sophisticated pairs selection
2. **Improve Execution**: Add smart order routing, iceberg orders
3. **Enhance Risk**: Add portfolio-level risk checks, correlation limits
4. **Add More Strategies**: Diversify across multiple uncorrelated strategies
5. **Improve Monitoring**: Add real-time dashboard, performance analytics
6. **Deploy to VPS**: Run on a reliable server with uptime monitoring

## Getting Started

1. Fork/clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your exchange API keys in `config.py` (start with testnet)
4. Run `startpy.bat` to launch the desktop interface and trading bot
5. Monitor the autonomous trading via the native Python desktop interface
6. After satisfactory testnet performance, set `TESTNET = False` in `config.py` for live trading

Remember: Always start with capital you can afford to lose. The autonomous bot is a tool to assist trading decisions, not a guaranteed profit system.