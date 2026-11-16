"""
Simulated price feed used when the real exchange is unreachable (offline
development, CI).

Prices are a pure function of wall-clock time, so every call is consistent:
the same bar always has the same OHLC regardless of the requested window.
BTC/ETH/SOL share common market waves and each adds its own slower
mean-reverting wave, giving the pairs strategy a spread that really oscillates.
"""
import time
import zlib

import numpy as np
import pandas as pd

_BASE = {"BTC/USDT": 65000.0, "ETH/USDT": 3200.0, "SOL/USDT": 150.0, "BNB/USDT": 580.0}
_TF_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400}

# (period in minutes, amplitude) of the shared market waves
_COMMON = [(1440.0, 0.020), (360.0, 0.014), (97.0, 0.012), (23.0, 0.006)]
# idiosyncratic waves, per symbol -> spread mean-reverts around zero
_IDIO = [(75.0, 0.0035), (31.0, 0.0020)]


def _seed(symbol: str) -> int:
    return zlib.crc32(symbol.encode()) % 100000


def _log_price_at(symbol: str, minute: float) -> float:
    s = _seed(symbol)
    v = 0.0
    for k, (period, amp) in enumerate(_COMMON):
        v += amp * np.sin(2 * np.pi * minute / period + 0.9 * k)
    for k, (period, amp) in enumerate(_IDIO):
        v += amp * np.sin(2 * np.pi * minute / period + (s % 628) / 100.0 + k)
    return v


def _noise(symbol: str, bar: int) -> float:
    rng = np.random.default_rng((_seed(symbol) * 1_000_003 + bar) % (2 ** 32))
    return float(rng.normal(0, 0.0006))


class SyntheticFeed:
    @staticmethod
    def _step(timeframe: str) -> int:
        return _TF_SECONDS.get(timeframe, 60)

    def _close(self, symbol: str, t_sec: float, step: int) -> float:
        bar = int(t_sec // step)
        base = _BASE.get(symbol, 100.0)
        return base * float(np.exp(_log_price_at(symbol, bar * step / 60.0) + _noise(symbol, bar)))

    def ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> pd.DataFrame:
        step = self._step(timeframe)
        now_bar = int(time.time() // step)
        rows = []
        for b in range(now_bar - limit + 1, now_bar + 1):
            t = b * step
            o = self._close(symbol, t - step, step)
            c = self._close(symbol, t, step)
            rng = np.random.default_rng((_seed(symbol) * 31 + b) % (2 ** 32))
            hi = max(o, c) * (1 + abs(rng.normal(0, 0.0005)))
            lo = min(o, c) * (1 - abs(rng.normal(0, 0.0005)))
            rows.append([t * 1000, o, hi, lo, c, float(rng.uniform(5, 60))])
        df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    def ticker(self, symbol: str) -> dict:
        """Cheap 24h ticker: samples the price function directly instead of building candles."""
        now = time.time()
        pts = [self._close(symbol, now - k * 3600, 60) for k in range(0, 25)]
        last = self._close(symbol, now, 60)
        first = pts[-1]
        return {
            "symbol": symbol,
            "last": last,
            "percentage": (last / first - 1) * 100,
            "high": max(pts + [last]),
            "low": min(pts + [last]),
            "quoteVolume": float(len(pts) * 5e7),
        }

    def order_book(self, symbol: str, limit: int = 20) -> dict:
        last = self.ticker(symbol)["last"]
        return {
            "bids": [[last * (1 - 0.0002 * (i + 1)), 1.0] for i in range(limit)],
            "asks": [[last * (1 + 0.0002 * (i + 1)), 1.0] for i in range(limit)],
        }
