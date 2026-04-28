import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import config
from utils import setup_logger
from data.storage import DataStorage

logger = setup_logger("RiskManager", "risk.log")

class RiskManager:
    def __init__(self, storage: DataStorage = None):
        self.storage = storage or DataStorage()
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.monthly_pnl = 0.0
        self.max_drawdown_reached = 0.0
        self.last_reset_daily = datetime.now().date()
        self.last_reset_weekly = datetime.now().date() - timedelta(days=datetime.now().weekday())
        self.last_reset_monthly = datetime.now().replace(day=1).date()
        
    def calculate_position_size(self, signal_price: float, stop_loss_price: float, 
                               account_balance: float = None, risk_percent: float = None) -> float:
        """
        Calculate position size based on risk per trade and stop loss distance.
        Formula: Position Size = (Account Balance * Risk %) / |Entry Price - Stop Loss Price|
        """
        if account_balance is None:
            account_balance = self.storage.get_portfolio_value()
        if risk_percent is None:
            risk_percent = config.RISK_PER_TRADE
        
        risk_amount = account_balance * risk_percent
        price_diff = abs(signal_price - stop_loss_price)
        
        if price_diff == 0:
            logger.warning("Stop loss price equals entry price, using minimum position size")
            return 0.0
            
        position_size = risk_amount / price_diff
        
        # Apply maximum position size limit
        max_position_value = account_balance * config.MAX_POSITION_SIZE
        max_position_size = max_position_value / signal_price if signal_price > 0 else 0
        
        if position_size > max_position_size:
            logger.warning(f"Position size {position_size:.6f} exceeds max {max_position_size:.6f}, capping")
            position_size = max_position_size
        
        return position_size
    
    def calculate_stop_loss(self, entry_price: float, side: str, atr: float = None, 
                           percent: float = None) -> float:
        """
        Calculate stop loss price based on ATR or fixed percentage.
        For long: stop = entry - (ATR * multiplier) or entry * (1 - percent)
        For short: stop = entry + (ATR * multiplier) or entry * (1 + percent)
        """
        if percent is None:
            percent = 0.02  # Default 2% stop loss
        
        if side.lower() == 'long':
            stop_loss = entry_price * (1 - percent)
        else:  # short
            stop_loss = entry_price * (1 + percent)
        
        return stop_loss
    
    def calculate_take_profit(self, entry_price: float, side: str, 
                             risk_reward_ratio: float = 2.0, 
                             stop_loss_price: float = None) -> float:
        """
        Calculate take profit price based on risk-reward ratio.
        """
        if stop_loss_price is None:
            # Default to 2% stop loss if not provided
            stop_loss_price = self.calculate_stop_loss(entry_price, side)
        
        risk = abs(entry_price - stop_loss_price)
        reward = risk * risk_reward_ratio
        
        if side.lower() == 'long':
            take_profit = entry_price + reward
        else:  # short
            take_profit = entry_price - reward
        
        return take_profit
    
    def check_daily_loss_limit(self, current_pnl: float) -> bool:
        """
        Check if daily loss limit has been breached.
        Returns True if trading should be halted.
        """
        today = datetime.now().date()
        if today != self.last_reset_daily:
            self.daily_pnl = 0.0
            self.last_reset_daily = today
        
        self.daily_pnl += current_pnl
        loss_limit = -config.INITIAL_CAPITAL * config.MAX_DAILY_LOSS
        
        if self.daily_pnl <= loss_limit:
            logger.warning(f"Daily loss limit breached: {self.daily_pnl:.2f} <= {loss_limit:.2f}")
            return True
        return False
    
    def check_weekly_loss_limit(self, current_pnl: float) -> bool:
        """
        Check if weekly loss limit has been breached.
        Returns True if trading should be halted.
        """
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        if week_start != self.last_reset_weekly:
            self.weekly_pnl = 0.0
            self.last_reset_weekly = week_start
        
        self.weekly_pnl += current_pnl
        loss_limit = -config.INITIAL_CAPITAL * config.MAX_WEEKLY_LOSS
        
        if self.weekly_pnl <= loss_limit:
            logger.warning(f"Weekly loss limit breached: {self.weekly_pnl:.2f} <= {loss_limit:.2f}")
            return True
        return False
    
    def check_monthly_loss_limit(self, current_pnl: float) -> bool:
        """
        Check if monthly loss limit has been breached.
        Returns True if trading should be halted.
        """
        today = datetime.now().date()
        month_start = today.replace(day=1)
        if month_start != self.last_reset_monthly:
            self.monthly_pnl = 0.0
            self.last_reset_monthly = month_start
        
        self.monthly_pnl += current_pnl
        loss_limit = -config.INITIAL_CAPITAL * config.MAX_MONTHLY_LOSS
        
        if self.monthly_pnl <= loss_limit:
            logger.warning(f"Monthly loss limit breached: {self.monthly_pnl:.2f} <= {loss_limit:.2f}")
            return True
        return False
    
    def check_max_drawdown(self, current_equity: float) -> bool:
        """
        Check if maximum drawdown has been breached.
        Returns True if trading should be halted.
        """
        peak_equity = self._get_peak_equity()
        if peak_equity == 0:
            peak_equity = config.INITIAL_CAPITAL
        
        drawdown = (peak_equity - current_equity) / peak_equity
        self.max_drawdown_reached = max(self.max_drawdown_reached, drawdown)
        
        if drawdown >= config.MAX_DRAWDOWN:
            logger.warning(f"Max drawdown breached: {drawdown:.2%} >= {config.MAX_DRAWDOWN:.2%}")
            return True
        return False
    
    def _get_peak_equity(self) -> float:
        """Get the peak equity from storage."""
        conn = self.storage.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(equity) FROM equity')
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else config.INITIAL_CAPITAL
    
    def check_position_limits(self, current_positions: List[Dict]) -> Tuple[bool, str]:
        """
        Check if we have exceeded maximum number of positions or position size limits.
        Returns (is_ok, reason)
        """
        if len(current_positions) >= config.MAX_POSITIONS:
            return False, f"Maximum positions ({config.MAX_POSITIONS}) reached"
        
        total_exposure = 0.0
        account_balance = self.storage.get_portfolio_value()
        
        for pos in current_positions:
            position_value = pos.get('size', 0) * pos.get('mark_price', 0)
            total_exposure += position_value
            
            # Check individual position size
            max_position_value = account_balance * config.MAX_POSITION_SIZE
            if position_value > max_position_value:
                return False, f"Position size exceeds maximum allowed: {position_value:.2f} > {max_position_value:.2f}"
        
        # Check total exposure
        max_total_exposure = account_balance * (config.MAX_POSITION_SIZE * config.MAX_POSITIONS)
        if total_exposure > max_total_exposure:
            return False, f"Total exposure exceeds maximum allowed: {total_exposure:.2f} > {max_total_exposure:.2f}"
        
        return True, ""
    
    def can_open_new_position(self, symbol: str, current_positions: List[Dict]) -> Tuple[bool, str]:
        """
        Determine if we can open a new position based on all risk checks.
        """
        # Check if we're already in a losing streak that should halt trading
        if self.check_daily_loss_limit(0) or self.check_weekly_loss_limit(0) or self.check_monthly_loss_limit(0):
            return False, "Loss limit breached"
        
        # Check current equity drawdown
        current_equity = self.storage.get_portfolio_value()
        if self.check_max_drawdown(current_equity):
            return False, "Maximum drawdown breached"
        
        # Check position limits
        is_ok, reason = self.check_position_limits(current_positions)
        if not is_ok:
            return False, reason
        
        # Check if we already have a position in this symbol (optional: allow multiple)
        # For now, we'll allow only one position per symbol to keep it simple
        for pos in current_positions:
            if pos.get('symbol') == symbol:
                return False, f"Already have an open position in {symbol}"
        
        return True, ""
    
    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics for monitoring."""
        current_equity = self.storage.get_portfolio_value()
        peak_equity = self._get_peak_equity()
        current_drawdown = (peak_equity - current_equity) / peak_equity if peak_equity > 0 else 0
        
        return {
            'current_equity': current_equity,
            'peak_equity': peak_equity,
            'current_drawdown': current_drawdown,
            'max_drawdown_reached': self.max_drawdown_reached,
            'daily_pnl': self.daily_pnl,
            'weekly_pnl': self.weekly_pnl,
            'monthly_pnl': self.monthly_pnl,
            'daily_limit_used': abs(self.daily_pnl) / (config.INITIAL_CAPITAL * config.MAX_DAILY_LOSS) if self.daily_pnl < 0 else 0,
            'weekly_limit_used': abs(self.weekly_pnl) / (config.INITIAL_CAPITAL * config.MAX_WEEKLY_LOSS) if self.weekly_pnl < 0 else 0,
            'monthly_limit_used': abs(self.monthly_pnl) / (config.INITIAL_CAPITAL * config.MAX_MONTHLY_LOSS) if self.monthly_pnl < 0 else 0,
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
