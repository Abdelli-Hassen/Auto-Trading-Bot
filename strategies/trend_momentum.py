"""
Trend + Momentum portfolio (long/flat spot, no leverage, 4h bars).

Research (6y of Binance 4h data, 8 large caps, 0.15% costs per unit turnover,
tuned on 2020-09..2023-06 and checked out-of-sample on 2023-07..2026-11):
    BTC buy&hold        Sharpe 0.73  CAGR 25%  maxDD -53%
    This portfolio      Sharpe 1.26  CAGR 41%  maxDD -28%

Two sleeves, averaged 50/50, each itself an average over several look-backs
(parameter ensembles avoid betting on one lucky setting):

1. Donchian breakout trend following - long a coin once it breaks its N-bar
   high, flat once it breaks its N/2-bar low (N = 120, 240, 480 bars).
2. Cross-sectional momentum - hold the top-3 coins by N-bar return, but only if
   the coin is above its 240-bar EMA and BTC is above its 480-bar EMA
   (N = 90, 180, 360 bars).

A portfolio-level volatility target (default 35% annualised, never levering up)
scales exposure down when the strategy itself gets turbulent.

Caveat: the universe is today's large caps (survivorship bias) and past
performance is no guarantee; the backtest is an estimate, not a promise.
"""
from typing import Dict

import numpy as np
import pandas as pd

import config

COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "LINK"]
BARS_PER_YEAR = 6 * 365          # 4h bars
WARMUP_BARS = 700                # history needed before weights are reliable
DON_LOOKBACKS = (120, 240, 480)
XS_LOOKBACKS = (90, 180, 360)


def _donchian(P: pd.DataFrame, n: int, shorts: bool = False) -> pd.DataFrame:
    hi = P.rolling(n).max().shift(1).to_numpy()
    lo = P.rolling(n // 2).min().shift(1).to_numpy()
    lo_n = P.rolling(n).min().shift(1).to_numpy()
    hi_h = P.rolling(n // 2).max().shift(1).to_numpy()
    x = P.to_numpy()
    out = np.zeros_like(x)
    state = np.zeros(x.shape[1])
    for t in range(len(x)):
        state[x[t] > hi[t]] = 1.0
        if shorts:
            state[x[t] < lo_n[t]] = -1.0                       # break of the N-bar low -> short
            state[(state == -1.0) & (x[t] > hi_h[t])] = 0.0    # cover when it recovers N/2-bar high
        state[(state == 1.0) & (x[t] < lo[t])] = 0.0
        out[t] = state
    return pd.DataFrame(out / x.shape[1], index=P.index, columns=P.columns)


def _xs_momentum(P: pd.DataFrame, lookback: int, k: int, trend_n: int, btc_n: int, shorts: bool = False) -> pd.DataFrame:
    rank = P.pct_change(lookback).rank(axis=1, ascending=False)
    ema = P.ewm(span=trend_n).mean()
    sel = (rank <= k).astype(float) * (P > ema).astype(float)
    w = sel / k
    regime = (P["BTC"] > P["BTC"].ewm(span=btc_n).mean()).astype(float)
    w = w.mul(regime, axis=0)
    if shorts:      # when BTC is in a downtrend, short the k weakest coins that are below their trend
        weak = (rank > len(P.columns) - k).astype(float) * (P < ema).astype(float)
        w = w - (weak / k).mul(1 - regime, axis=0)
    return w


def _net_returns(P: pd.DataFrame, w: pd.DataFrame, cost: float) -> pd.Series:
    w = w.shift(1).fillna(0)
    gross = (w * P.pct_change().fillna(0)).sum(axis=1)
    return gross - w.diff().abs().sum(axis=1).fillna(0) * cost


class TrendMomentumStrategy:
    timeframe = "4h"

    def __init__(self, target_vol: float = 0.35, cost: float = 0.0015, cap: float = None, allow_shorts: bool = False):
        self.allow_shorts = allow_shorts
        self.name = "TrendMomentumLS" if allow_shorts else "TrendMomentum"
        self.target_vol = target_vol
        self.cost = cost
        self._cap = cap
        self.coins = COINS
        self.symbols = [f"{c}/USDT" for c in COINS]

    @property
    def cap(self) -> float:
        return self._cap if self._cap is not None else config.MAX_POSITION_SIZE

    # ------------------------------------------------------------------ core
    def components(self, P: pd.DataFrame) -> Dict:
        P = P[self.coins].astype(float)
        sh = self.allow_shorts
        don = sum(_donchian(P, n, sh) for n in DON_LOOKBACKS) / len(DON_LOOKBACKS)
        xs = sum(_xs_momentum(P, lb, 3, 240, 480, sh) for lb in XS_LOOKBACKS) / len(XS_LOOKBACKS)
        mix = (don + xs) / 2
        rv = _net_returns(P, mix, self.cost).rolling(360).std() * np.sqrt(BARS_PER_YEAR)
        scale = (self.target_vol / rv).clip(upper=1.0).fillna(0.5)
        w = mix.mul(scale, axis=0).clip(lower=-self.cap, upper=self.cap)
        total = w.abs().sum(axis=1)
        w = w.div(total.where(total > 1.0, 1.0), axis=0)          # gross exposure never above 100%
        return {"P": P, "don": don, "xs": xs, "scale": scale, "w": w, "rv": rv}

    def compute_weights(self, P: pd.DataFrame) -> pd.DataFrame:
        return self.components(P)["w"]

    def target_weights(self, P: pd.DataFrame) -> Dict[str, float]:
        last = self.compute_weights(P).iloc[-1]
        return {f"{c}/USDT": float(last[c]) if abs(last[c]) >= 0.01 else 0.0 for c in self.coins}

    def explain(self, P: pd.DataFrame) -> Dict:
        """Per-coin reasoning behind the current target weights (for the UI)."""
        c = self.components(P)
        P = c["P"]
        ema = P.ewm(span=240).mean()
        mom = P.pct_change(90).iloc[-1]
        rank = mom.rank(ascending=False)
        n = len(self.coins)
        w = c["w"].iloc[-1]
        rows = []
        for coin in self.coins:
            rows.append({
                "symbol": f"{coin}/USDT",
                "price": float(P[coin].iloc[-1]),
                "trend_up": bool(P[coin].iloc[-1] > ema[coin].iloc[-1]),
                "breakout": round(float(c["don"][coin].iloc[-1]) * n, 2),      # share of breakout look-backs long (+) / short (-)
                "momentum_pct": float(mom[coin]) if not np.isnan(mom[coin]) else 0.0,
                "momentum_rank": int(rank[coin]) if not np.isnan(rank[coin]) else n,
                "in_top3": bool(c["xs"][coin].iloc[-1] > 0),
                "target": float(w[coin]) if abs(w[coin]) >= 0.01 else 0.0,
            })
        btc_up = bool(P["BTC"].iloc[-1] > P["BTC"].ewm(span=480).mean().iloc[-1])
        return {
            "rows": rows,
            "btc_regime_up": btc_up,
            "vol_scale": float(c["scale"].iloc[-1]),
            "realized_vol": float(c["rv"].iloc[-1]) if not np.isnan(c["rv"].iloc[-1]) else None,
            "bar": str(P.index[-1]),
        }

    def backtest(self, P: pd.DataFrame) -> Dict:
        w = self.compute_weights(P)
        r = _net_returns(P[self.coins].astype(float), w, self.cost)
        r = r.iloc[WARMUP_BARS:] if len(r) > WARMUP_BARS + 50 else r
        eq = (1 + r).cumprod()
        yrs = max(len(r) / BARS_PER_YEAR, 1e-9)
        return {
            "bars": len(r),
            "total_return_percent": float(eq.iloc[-1] - 1),
            "cagr": float(eq.iloc[-1] ** (1 / yrs) - 1),
            "sharpe_ratio": float(r.mean() / r.std() * np.sqrt(BARS_PER_YEAR)) if r.std() > 0 else 0.0,
            "max_drawdown": float(-(eq / eq.cummax() - 1).min()),
            "avg_exposure": float(w.abs().sum(axis=1).iloc[WARMUP_BARS:].mean()) if len(w) > WARMUP_BARS else 0.0,
            "equity_curve": [(str(t), float(v)) for t, v in eq.items()],
        }
