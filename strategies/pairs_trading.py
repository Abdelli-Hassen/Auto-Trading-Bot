"""
Pairs trading (statistical arbitrage) on a log-price spread.

    spread = ln(P1) - beta * ln(P2) - alpha        (beta/alpha from rolling OLS)
    z      = spread / residual_std

z < -ENTRY  -> long the spread  (buy symbol 1, short symbol 2)
z > +ENTRY  -> short the spread (sell symbol 1, buy symbol 2)
|z| < EXIT  -> close (mean reverted)
adverse |z| > STOP -> stop out
"""
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

import config
from .base import BaseStrategy
from utils import setup_logger

logger = setup_logger("PairsTrading", "pairs_trading.log")

LONG, SHORT = "long", "short"   # direction of the *spread* position


class PairsTradingStrategy(BaseStrategy):
    def __init__(self, pair: Tuple[str, str] = ("BTC/USDT", "ETH/USDT"), window: int = 60):
        super().__init__("PairsTrading")
        self.pair = pair
        self.symbol1, self.symbol2 = pair
        self.window = window
        self.lookback_period = window
        self.entry_zscore = config.ENTRY_THRESHOLD
        self.exit_zscore = config.EXIT_THRESHOLD
        self.stop_zscore = config.STOP_THRESHOLD
        self.hedge_ratio: Optional[float] = None
        self.spread_mean: Optional[float] = None
        self.spread_std: Optional[float] = None
        self.last_zscore: float = 0.0

    # ------------------------------------------------------------ statistics
    def rolling_zscore(self, price1: pd.Series, price2: pd.Series,
                       window: int = None) -> pd.DataFrame:
        """Vectorised rolling hedge ratio and spread z-score (log prices)."""
        w = window or self.window
        l1 = np.log(price1.astype(float).reset_index(drop=True))
        l2 = np.log(price2.astype(float).reset_index(drop=True))
        m1, m2 = l1.rolling(w).mean(), l2.rolling(w).mean()
        v1, v2 = l1.rolling(w).var(), l2.rolling(w).var()
        cov = l1.rolling(w).cov(l2)
        beta = cov / v2.replace(0, np.nan)
        resid_var = (v1 - cov ** 2 / v2.replace(0, np.nan)).clip(lower=0)
        resid_std = np.sqrt(resid_var).replace(0, np.nan)
        alpha = m1 - beta * m2
        spread = l1 - beta * l2 - alpha
        z = (spread / resid_std).replace([np.inf, -np.inf], np.nan)
        return pd.DataFrame({"beta": beta, "spread": spread, "std": resid_std, "z": z})

    def analyze(self, price1: pd.Series, price2: pd.Series) -> Dict:
        """Latest statistics, used by the live loop."""
        if len(price1) < max(self.window, 10) or len(price2) < max(self.window, 10):
            return {"ready": False, "z": 0.0, "beta": None}
        stats = self.rolling_zscore(price1, price2, min(self.window, len(price1))).iloc[-1]
        # A non-positive hedge ratio means the pair is not co-moving: never trade it.
        if np.isnan(stats["z"]) or stats["beta"] <= 0.05:
            return {"ready": False, "z": 0.0, "beta": None}
        self.hedge_ratio = float(stats["beta"])
        self.spread_mean = 0.0
        self.spread_std = float(stats["std"])
        self.last_zscore = float(stats["z"])
        return {"ready": True, "z": self.last_zscore, "beta": self.hedge_ratio,
                "spread": float(stats["spread"]), "std": self.spread_std}

    # -------------------------------------------------------------- decision
    @staticmethod
    def round_trip_cost() -> float:
        """Cost of opening+closing both legs, as a fraction of one leg's notional."""
        return 4 * (config.FEE_RATE + config.SLIPPAGE)

    def has_edge(self, std: Optional[float]) -> bool:
        """Expected reversion (entry->exit in z units * residual std) must beat costs."""
        if std is None or np.isnan(std):
            return True
        return (self.entry_zscore - self.exit_zscore) * std >= config.MIN_EDGE_MULT * self.round_trip_cost()

    def decide(self, z: float, current: Optional[str], std: Optional[float] = None) -> str:
        """
        current: None | 'long' | 'short' (spread position).
        std: residual spread std; when given, entries without a cost-beating edge are skipped.
        Returns one of: open_long, open_short, close, stop, hold.
        """
        if current is None:
            if not self.has_edge(std):
                return "hold"
            if z <= -self.entry_zscore:
                return "open_long"
            if z >= self.entry_zscore:
                return "open_short"
            return "hold"
        if current == LONG and z <= -self.stop_zscore:
            return "stop"
        if current == SHORT and z >= self.stop_zscore:
            return "stop"
        if abs(z) <= self.exit_zscore:
            return "close"
        return "hold"

    # ------------------------------------------------------------ BaseStrategy
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Entry signals per bar (+1 long spread, -1 short spread, 0 none).
        Expects columns '<sym1>_close' and '<sym2>_close'.
        """
        cols = ["signal", "entry_price", "stop_loss", "take_profit"]
        c1, c2 = f"{self.symbol1}_close", f"{self.symbol2}_close"
        if data.empty or c1 not in data.columns or c2 not in data.columns:
            return pd.DataFrame(columns=cols)
        z = self.rolling_zscore(data[c1], data[c2])["z"].to_numpy()
        signals = pd.DataFrame(0.0, index=data.index, columns=cols)
        sig = np.where(z <= -self.entry_zscore, 1, np.where(z >= self.entry_zscore, -1, 0))
        signals["signal"] = np.nan_to_num(sig)
        signals["entry_price"] = data[c1].to_numpy()
        return signals

    def calculate_position_size(self, signal: Dict, account_balance: float) -> float:
        """Dollar-neutral: each leg gets MAX_POSITION_SIZE of equity; returns base units of leg 1."""
        price = signal.get("entry_price", 0)
        if signal.get("signal", 0) == 0 or price <= 0:
            return 0.0
        return account_balance * config.MAX_POSITION_SIZE / price
