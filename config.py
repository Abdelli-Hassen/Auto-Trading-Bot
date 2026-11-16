"""
Central configuration for the trading bot.

Everything here is PAPER TRADING ONLY: orders are simulated locally against
live (public) market prices. No API keys are needed and no real money is ever
at risk. Values can be overridden with environment variables or a `.env` file.
"""
import os
from pathlib import Path

try:  # optional dependency
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # pragma: no cover
    pass


def _env(name, default, cast=str):
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        if cast is bool:
            return raw.strip().lower() in ("1", "true", "yes", "on")
        return cast(raw)
    except ValueError:
        return default


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# --- Mode -----------------------------------------------------------------
# The bot never routes orders to a real exchange. Kept as a constant so that
# the whole system is explicit about it.
PAPER_TRADING = True
TESTNET = True

# --- Market data ------------------------------------------------------------
EXCHANGE = _env("EXCHANGE", "binance")
API_KEY = ""        # intentionally unused: public market data only
API_SECRET = ""
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "LINK/USDT"]
TIMEFRAME = _env("TIMEFRAME", "1m")
# If the exchange is unreachable, fall back to a simulated price feed so the
# bot stays fully usable offline.
# Set FORCE_SYNTHETIC=true to always use the simulated feed (demo / offline).
FORCE_SYNTHETIC = _env("FORCE_SYNTHETIC", False, bool)
# DANGER: the simulated feed uses made-up prices. Falling back to it while holding positions opened at real
# prices corrupts the account (this wiped a paper account overnight). Keep this False; use FORCE_SYNTHETIC for demos.
ALLOW_SYNTHETIC_FALLBACK = _env("ALLOW_SYNTHETIC_FALLBACK", False, bool)

# --- Paper account ----------------------------------------------------------
INITIAL_CAPITAL = _env("INITIAL_CAPITAL", 10000.0, float)
FEE_RATE = _env("FEE_RATE", 0.0004, float)         # 0.04% per fill (taker, futures-style)
SLIPPAGE = _env("SLIPPAGE", 0.0001, float)         # 0.01% adverse fill
CYCLE_SECONDS = _env("CYCLE_SECONDS", 15, int)
# Trading budget: the strategy sizes positions against min(equity * TRADE_BUDGET_PCT, TRADE_BUDGET_USD).
# TRADE_BUDGET_USD = 0 means no dollar cap. The rest of the account stays in cash.
TRADE_BUDGET_PCT = _env("TRADE_BUDGET_PCT", 1.0, float)
TRADE_BUDGET_USD = _env("TRADE_BUDGET_USD", 0.0, float)
# Fixed dollars per position (0 = off). When set, every coin the strategy wants to hold gets exactly this
# amount (long or short) instead of a weight-based share, still limited by the trading budget.
TRADE_SIZE_USD = _env("TRADE_SIZE_USD", 0.0, float)

# "trend_momentum" (default, multi-coin trend + momentum portfolio) or "pairs"
STRATEGY = _env("STRATEGY", "trend_momentum")
REBALANCE_THRESHOLD = _env("REBALANCE_THRESHOLD", 0.02, float)  # min weight change worth trading

# --- Strategy (pairs trading, z-score mean reversion) ------------------------
ENTRY_THRESHOLD = _env("ENTRY_THRESHOLD", 2.0, float)
EXIT_THRESHOLD = _env("EXIT_THRESHOLD", 0.5, float)
STOP_THRESHOLD = _env("STOP_THRESHOLD", 3.0, float)
# Only enter when the expected mean-reversion profit is at least this multiple of
# the round-trip trading cost (fees + slippage on 4 fills).
MIN_EDGE_MULT = _env("MIN_EDGE_MULT", 1.5, float)

# --- Risk -------------------------------------------------------------------
RISK_PER_TRADE = _env("RISK_PER_TRADE", 0.01, float)
MAX_POSITION_SIZE = _env("MAX_POSITION_SIZE", 0.30, float)   # of equity, per coin / pair leg
MAX_POSITIONS = _env("MAX_POSITIONS", 8, int)
MAX_DAILY_LOSS = _env("MAX_DAILY_LOSS", 0.03, float)
MAX_WEEKLY_LOSS = _env("MAX_WEEKLY_LOSS", 0.07, float)
MAX_MONTHLY_LOSS = _env("MAX_MONTHLY_LOSS", 0.12, float)
MAX_DRAWDOWN = _env("MAX_DRAWDOWN", 0.30, float)
