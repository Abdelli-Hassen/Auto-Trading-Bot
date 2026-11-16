"""
Pairs-trading backtester.

Replays historical bars through exactly the same decision logic and the same
PaperAccount (fees + slippage) that the live paper bot uses.
"""
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

import config
from data.fetcher import DataFetcher
from execution.paper import PaperAccount
from utils import setup_logger, calculate_sharpe, calculate_max_drawdown

logger = setup_logger("BacktestEngine", "backtest.log")

_BARS_PER_YEAR = {"1m": 525600, "5m": 105120, "15m": 35040, "30m": 17520,
                  "1h": 8760, "4h": 2190, "1d": 365}


class BacktestEngine:
    def __init__(self, initial_capital: float = config.INITIAL_CAPITAL, data_fetcher: DataFetcher = None):
        self.initial_capital = initial_capital
        self.data_fetcher = data_fetcher or DataFetcher()
        self.trades: List[Dict] = []
        self.equity_curve: List = []

    def run_backtest(self, strategy, start_date: str, end_date: str, timeframe: str = "1h") -> Dict:
        s1, s2 = strategy.pair
        logger.info(f"Backtest {strategy.name} {s1}/{s2} {start_date} -> {end_date} [{timeframe}]")
        d1 = self.data_fetcher.get_historical_data(s1, start_date, end_date, timeframe)
        d2 = self.data_fetcher.get_historical_data(s2, start_date, end_date, timeframe)
        if d1.empty or d2.empty:
            raise ValueError("No historical data available for the requested range")
        merged = pd.merge(d1[['timestamp', 'close']], d2[['timestamp', 'close']],
                          on='timestamp', suffixes=('_1', '_2')).dropna().reset_index(drop=True)
        if len(merged) < strategy.window + 5:
            raise ValueError(f"Not enough overlapping bars ({len(merged)}) for window {strategy.window}")
        return self.run_on_frame(strategy, merged, timeframe)

    def run_portfolio(self, strategy, start_date: str, end_date: str) -> Dict:
        """Backtest the trend+momentum portfolio on real 4h history (incl. warm-up)."""
        from datetime import datetime, timedelta
        warm_start = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=130)).strftime("%Y-%m-%d")
        closes = {}
        for sym in strategy.symbols:
            df = self.data_fetcher.get_historical_data(sym, warm_start, end_date, strategy.timeframe)
            if df.empty:
                raise ValueError(f"No historical data for {sym}")
            closes[sym.split("/")[0]] = df.set_index("timestamp")["close"]
        P = pd.DataFrame(closes).dropna()
        res = strategy.backtest(P)
        start = pd.Timestamp(start_date)
        curve = [(t, v) for t, v in res["equity_curve"] if pd.Timestamp(t) >= start] or res["equity_curve"]
        base = curve[0][1]
        curve = [(t, self.initial_capital * v / base) for t, v in curve]
        final = curve[-1][1]
        res.update({
            "initial_capital": self.initial_capital, "final_capital": final,
            "total_return": final - self.initial_capital,
            "total_return_percent": final / self.initial_capital - 1,
            "equity_curve": curve, "trades": [], "total_trades": 0, "win_rate": 0.0,
            "profit_factor": 0.0, "winning_trades": 0, "losing_trades": 0, "fees_paid": 0.0,
        })
        return res

    def run_on_frame(self, strategy, frame: pd.DataFrame, timeframe: str = "1h") -> Dict:
        """frame: columns timestamp, close_1, close_2."""
        s1, s2 = strategy.pair
        acct = PaperAccount(self.initial_capital)
        roll = strategy.rolling_zscore(frame['close_1'], frame['close_2'])
        z, stds = roll['z'].to_numpy(), roll['std'].to_numpy()
        p1, p2 = frame['close_1'].to_numpy(), frame['close_2'].to_numpy()
        ts = frame['timestamp']
        self.trades, self.equity_curve = [], []
        spread_pos: Optional[str] = None
        pair_pnl = 0.0
        pair_open_eq = 0.0

        def close_pair(i, reason):
            nonlocal spread_pos
            pnl = 0.0
            for sym, px in ((s1, p1[i]), (s2, p2[i])):
                fill = acct.close_position(sym, px, reason)
                if fill:
                    pnl += fill['pnl']
            self.trades.append({"exit_time": str(ts.iloc[i]), "pnl": pnl, "reason": reason,
                                "side": spread_pos, "entry_time": entry_time})
            spread_pos = None

        entry_time = None
        for i in range(len(frame)):
            acct.mark({s1: p1[i], s2: p2[i]})
            zi = z[i]
            if not np.isnan(zi):
                action = strategy.decide(float(zi), spread_pos, float(stds[i]))
                if spread_pos is not None and acct.unrealized_pnl() <= -2 * config.RISK_PER_TRADE * pair_open_eq:
                    action = "stop"
                if action in ("close", "stop"):
                    close_pair(i, "mean_reversion" if action == "close" else "stop_loss")
                elif action in ("open_long", "open_short") and spread_pos is None:
                    eq = acct.equity()
                    notional = eq * config.MAX_POSITION_SIZE
                    long_s = action == "open_long"
                    a = acct.open_position(s1, "long" if long_s else "short", notional / p1[i], p1[i])
                    b = acct.open_position(s2, "short" if long_s else "long", notional / p2[i], p2[i])
                    if a and b:
                        spread_pos = "long" if long_s else "short"
                        pair_open_eq = eq
                        entry_time = str(ts.iloc[i])
            self.equity_curve.append((str(ts.iloc[i]), acct.equity()))
        if spread_pos is not None:
            acct.mark({s1: p1[-1], s2: p2[-1]})
            close_pair(len(frame) - 1, "end_of_backtest")
            self.equity_curve[-1] = (str(ts.iloc[-1]), acct.equity())

        return self._results(acct, timeframe)

    def _results(self, acct: PaperAccount, timeframe: str) -> Dict:
        final = acct.equity()
        pnls = [t['pnl'] for t in self.trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        eq = [e for _, e in self.equity_curve]
        rets = list(np.diff(eq) / np.array(eq[:-1])) if len(eq) > 1 else []
        sharpe = calculate_sharpe(rets) * np.sqrt(_BARS_PER_YEAR.get(timeframe, 8760) / 252) if rets else 0.0
        gross_loss = abs(sum(losses))
        return {
            'initial_capital': self.initial_capital,
            'final_capital': final,
            'total_return': final - self.initial_capital,
            'total_return_percent': (final - self.initial_capital) / self.initial_capital,
            'total_trades': len(pnls),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': len(wins) / len(pnls) if pnls else 0.0,
            'profit_factor': (sum(wins) / gross_loss) if gross_loss > 0 else (sum(wins) if wins else 0.0),
            'sharpe_ratio': float(np.clip(sharpe, -99, 99)),
            'max_drawdown': calculate_max_drawdown(eq),
            'fees_paid': acct.fees_paid,
            'bars': len(eq),
            'equity_curve': self.equity_curve,
            'trades': self.trades,
        }
