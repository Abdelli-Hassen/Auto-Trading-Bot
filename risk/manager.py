from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

import config
from data.storage import DataStorage
from utils import setup_logger

logger = setup_logger("RiskManager", "risk.log")


class RiskManager:
    """
    Position sizing, loss limits and drawdown protection.

    `equity_provider` is a callable returning current account equity (the paper
    account). Without one, the last stored equity snapshot is used.
    """

    def __init__(self, storage: DataStorage = None, equity_provider=None):
        self.storage = storage or DataStorage()
        self.equity_provider = equity_provider
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.monthly_pnl = 0.0
        self.max_drawdown_reached = 0.0
        self.last_reset_daily = datetime.now().date()
        self.last_reset_weekly = datetime.now().date() - timedelta(days=datetime.now().weekday())
        self.last_reset_monthly = datetime.now().replace(day=1).date()
        self.halted_reason: Optional[str] = None
        self.peak_adjust = 0.0      # shifts the equity peak when funds are deposited / withdrawn

    # ---------------------------------------------------------------- equity
    def current_equity(self) -> float:
        if self.equity_provider:
            return float(self.equity_provider())
        return self.storage.get_portfolio_value()

    def _get_peak_equity(self) -> float:
        conn = self.storage.get_connection()
        result = conn.execute("SELECT MAX(equity) FROM equity").fetchone()[0]
        conn.close()
        return max((result or 0.0) + self.peak_adjust, config.INITIAL_CAPITAL)

    # ---------------------------------------------------------------- sizing
    def calculate_position_size(self, signal_price: float, stop_loss_price: float,
                                account_balance: float = None, risk_percent: float = None) -> float:
        """Units such that hitting the stop loses `risk_percent` of the account, capped by max size."""
        if account_balance is None:
            account_balance = self.current_equity()
        if risk_percent is None:
            risk_percent = config.RISK_PER_TRADE
        price_diff = abs(signal_price - stop_loss_price)
        if price_diff == 0 or signal_price <= 0:
            return 0.0
        size = account_balance * risk_percent / price_diff
        max_size = account_balance * config.MAX_POSITION_SIZE / signal_price
        return min(size, max_size)

    def pair_notional(self, equity: float = None) -> float:
        """Dollar value allocated to each leg of a dollar-neutral pair trade."""
        equity = self.current_equity() if equity is None else equity
        return max(equity, 0.0) * config.MAX_POSITION_SIZE

    def calculate_stop_loss(self, entry_price: float, side: str, atr: float = None,
                            percent: float = None) -> float:
        percent = 0.02 if percent is None else percent
        return entry_price * (1 - percent) if side.lower() == 'long' else entry_price * (1 + percent)

    def calculate_take_profit(self, entry_price: float, side: str, risk_reward_ratio: float = 2.0,
                              stop_loss_price: float = None) -> float:
        if stop_loss_price is None:
            stop_loss_price = self.calculate_stop_loss(entry_price, side)
        reward = abs(entry_price - stop_loss_price) * risk_reward_ratio
        return entry_price + reward if side.lower() == 'long' else entry_price - reward

    # ------------------------------------------------------- PnL accounting
    def _roll_periods(self):
        today = datetime.now().date()
        if today != self.last_reset_daily:
            self.reset_daily_pnl()
        week_start = today - timedelta(days=today.weekday())
        if week_start != self.last_reset_weekly:
            self.reset_weekly_pnl()
        if today.replace(day=1) != self.last_reset_monthly:
            self.reset_monthly_pnl()

    def record_pnl(self, pnl: float):
        """Feed realised PnL of a closed trade into the loss-limit counters."""
        self._roll_periods()
        self.daily_pnl += pnl
        self.weekly_pnl += pnl
        self.monthly_pnl += pnl

    def check_daily_loss_limit(self, current_pnl: float = 0.0) -> bool:
        self._roll_periods()
        self.daily_pnl += current_pnl
        return self.daily_pnl <= -config.INITIAL_CAPITAL * config.MAX_DAILY_LOSS

    def check_weekly_loss_limit(self, current_pnl: float = 0.0) -> bool:
        self._roll_periods()
        self.weekly_pnl += current_pnl
        return self.weekly_pnl <= -config.INITIAL_CAPITAL * config.MAX_WEEKLY_LOSS

    def check_monthly_loss_limit(self, current_pnl: float = 0.0) -> bool:
        self._roll_periods()
        self.monthly_pnl += current_pnl
        return self.monthly_pnl <= -config.INITIAL_CAPITAL * config.MAX_MONTHLY_LOSS

    def check_max_drawdown(self, current_equity: float) -> bool:
        peak = max(self._get_peak_equity(), current_equity)
        drawdown = (peak - current_equity) / peak if peak else 0.0
        self.max_drawdown_reached = max(self.max_drawdown_reached, drawdown)
        return drawdown >= config.MAX_DRAWDOWN

    def check_position_limits(self, current_positions: List[Dict]) -> Tuple[bool, str]:
        if len(current_positions) >= config.MAX_POSITIONS:
            return False, f"Maximum positions ({config.MAX_POSITIONS}) reached"
        return True, ""

    def can_open_new_position(self, symbol: str, current_positions: List[Dict]) -> Tuple[bool, str]:
        """All pre-trade risk checks. Returns (allowed, reason)."""
        if self.check_daily_loss_limit(0):
            return False, "Daily loss limit breached"
        if self.check_weekly_loss_limit(0):
            return False, "Weekly loss limit breached"
        if self.check_monthly_loss_limit(0):
            return False, "Monthly loss limit breached"
        if self.check_max_drawdown(self.current_equity()):
            return False, "Maximum drawdown breached"
        # a pair needs room for two legs
        if len(current_positions) + 2 > max(config.MAX_POSITIONS, 2):
            return False, f"Maximum positions ({config.MAX_POSITIONS}) reached"
        for pos in current_positions:
            if pos.get('symbol') == symbol:
                return False, f"Already have an open position in {symbol}"
        return True, ""

    # --------------------------------------------------------------- metrics
    def get_risk_metrics(self) -> Dict:
        self._roll_periods()
        equity = self.current_equity()
        peak = max(self._get_peak_equity(), equity)
        drawdown = (peak - equity) / peak if peak > 0 else 0.0
        self.max_drawdown_reached = max(self.max_drawdown_reached, drawdown)

        series = self.storage.get_equity_series()
        sharpe = 0.0
        if len(series) > 3:
            arr = np.array(series, dtype=float)
            rets = np.diff(arr) / np.where(arr[:-1] == 0, np.nan, arr[:-1])
            rets = rets[~np.isnan(rets)]
            if len(rets) > 2 and rets.std() > 0:
                # samples are ~cycle-spaced: annualise by samples per year
                per_year = (365 * 24 * 3600) / max(config.CYCLE_SECONDS, 1)
                sharpe = float(rets.mean() / rets.std() * np.sqrt(per_year))
                sharpe = float(np.clip(sharpe, -99, 99))

        pnls = self.storage.get_trade_pnls()
        wins = sum(p for p in pnls if p > 0)
        losses = abs(sum(p for p in pnls if p < 0))
        profit_factor = wins / losses if losses > 0 else (wins if wins > 0 else 0.0)

        def used(pnl, limit):
            return abs(pnl) / (config.INITIAL_CAPITAL * limit) if pnl < 0 else 0

        return {
            'current_equity': equity,
            'peak_equity': peak,
            'current_drawdown': drawdown,
            'max_drawdown_reached': self.max_drawdown_reached,
            'total_pnl': equity - config.INITIAL_CAPITAL,
            'daily_pnl': self.daily_pnl,
            'weekly_pnl': self.weekly_pnl,
            'monthly_pnl': self.monthly_pnl,
            'daily_limit_used': used(self.daily_pnl, config.MAX_DAILY_LOSS),
            'weekly_limit_used': used(self.weekly_pnl, config.MAX_WEEKLY_LOSS),
            'monthly_limit_used': used(self.monthly_pnl, config.MAX_MONTHLY_LOSS),
            'sharpe_ratio': sharpe,
            'profit_factor': float(profit_factor),
            'halted_reason': self.halted_reason,
            'limits': {'daily': config.MAX_DAILY_LOSS, 'weekly': config.MAX_WEEKLY_LOSS,
                       'monthly': config.MAX_MONTHLY_LOSS, 'drawdown': config.MAX_DRAWDOWN},
        }

    def reset_daily_pnl(self):
        self.daily_pnl = 0.0
        self.last_reset_daily = datetime.now().date()

    def reset_weekly_pnl(self):
        self.weekly_pnl = 0.0
        self.last_reset_weekly = datetime.now().date() - timedelta(days=datetime.now().weekday())

    def reset_monthly_pnl(self):
        self.monthly_pnl = 0.0
        self.last_reset_monthly = datetime.now().replace(day=1).date()

    def reset_all(self):
        self.reset_daily_pnl()
        self.reset_weekly_pnl()
        self.reset_monthly_pnl()
        self.max_drawdown_reached = 0.0
        self.halted_reason = None
        self.peak_adjust = 0.0
