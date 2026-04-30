import pandas as pd
import numpy as np
import statsmodels.api as sm
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import config
from .base import BaseStrategy
from utils import setup_logger

logger = setup_logger("PairsTrading", "pairs_trading.log")

class PairsTradingStrategy(BaseStrategy):
    def __init__(self, pair: Tuple[str, str] = ("BTC/USDT", "ETH/USDT")):
        super().__init__("PairsTrading")
        self.pair = pair
        self.symbol1, self.symbol2 = pair
        self.hedge_ratio = None
        self.spread_mean = None
        self.spread_std = None
        self.lookback_period = 30  # days for calculating hedge ratio
        self.entry_zscore = config.ENTRY_THRESHOLD  # 2.0
        self.exit_zscore = config.EXIT_THRESHOLD   # 0.5
        self.stop_zscore = config.STOP_THRESHOLD   # 3.0
        
    def calculate_hedge_ratio(self, price1: pd.Series, price2: pd.Series) -> float:
        """
        Calculate hedge ratio using linear regression.
        price1 = hedge_ratio * price2 + intercept
        """
        if len(price1) < 2 or len(price2) < 2:
            return 1.0
            
        X = sm.add_constant(price2)
        model = sm.OLS(price1, X).fit()
        self.hedge_ratio = model.params.iloc[1]  # slope coefficient
        return self.hedge_ratio
    
    def calculate_spread(self, price1: pd.Series, price2: pd.Series) -> pd.Series:
        """
        Calculate spread: price1 - hedge_ratio * price2
        """
        if self.hedge_ratio is None:
            self.hedge_ratio = self.calculate_hedge_ratio(price1, price2)
        
        spread = price1 - self.hedge_ratio * price2
        return spread
    
    def update_spread_stats(self, spread: pd.Series):
        """Update mean and standard deviation of spread."""
        if len(spread) >= 2:
            self.spread_mean = spread.mean()
            self.spread_std = spread.std()
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate signals based on pairs trading strategy.
        Expects data to have columns: ['timestamp', 'BTC/USDT_close', 'ETH/USDT_close']
        """
        if data.empty or len(data) < 2:
            return pd.DataFrame(columns=['signal', 'entry_price', 'stop_loss', 'take_profit'])
        
        # Check if we have the required price columns
        symbol1_col = f'{self.symbol1}_close'
        symbol2_col = f'{self.symbol2}_close'
        
        if symbol1_col not in data.columns or symbol2_col not in data.columns:
            logger.warning(f"Missing price columns for {self.symbol1} ({symbol1_col}) or {self.symbol2} ({symbol2_col})")
            logger.warning(f"Available columns: {list(data.columns)}")
            return pd.DataFrame(columns=['signal', 'entry_price', 'stop_loss', 'take_profit'])
        
        price1 = data[symbol1_col]
        price2 = data[symbol2_col]
        
        # Calculate hedge ratio and spread
        self.calculate_hedge_ratio(price1, price2)
        spread = self.calculate_spread(price1, price2)
        
        # Update statistics
        self.update_spread_stats(spread)
        
        if self.spread_std == 0 or np.isnan(self.spread_std):
            logger.warning("Spread standard deviation is zero or NaN")
            return pd.DataFrame(columns=['signal', 'entry_price', 'stop_loss', 'take_profit'])
        
        # Calculate z-score
        zscore = (spread - self.spread_mean) / self.spread_std
        
        # Initialize signals DataFrame
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        signals['entry_price'] = 0.0
        signals['stop_loss'] = 0.0
        signals['take_profit'] = 0.0
        
        # Generate signals based on z-score
        for i in range(len(data)):
            current_zscore = zscore.iloc[i] if not np.isnan(zscore.iloc[i]) else 0
            
            # Long signal: spread is significantly negative (expect reversion to mean)
            if current_zscore < -self.entry_zscore:
                signals.iloc[i, signals.columns.get_loc('signal')] = 1  # Long spread (buy symbol1, sell symbol2)
                signals.iloc[i, signals.columns.get_loc('entry_price')] = price1.iloc[i]  # Entry for symbol1
                # For pairs trading, we need to think about actual prices
                # We'll use symbol1 price as reference for position sizing
                
                # Calculate stop loss and take profit based on z-score reversion
                stop_loss_spread = self.spread_mean - self.stop_zscore * self.spread_std
                take_profit_spread = self.spread_mean  # Revert to mean
                
                # Convert spread levels back to price levels for symbol1
                # spread = price1 - hedge_ratio * price2
                # For stop loss: price1_stop = stop_loss_spread + hedge_ratio * price2
                price2_at_point = price2.iloc[i]
                stop_loss_price1 = stop_loss_spread + self.hedge_ratio * price2_at_point
                take_profit_price1 = take_profit_spread + self.hedge_ratio * price2_at_point
                
                signals.iloc[i, signals.columns.get_loc('stop_loss')] = stop_loss_price1
                signals.iloc[i, signals.columns.get_loc('take_profit')] = take_profit_price1
                
            # Short signal: spread is significantly positive (expect reversion to mean)
            elif current_zscore > self.entry_zscore:
                signals.iloc[i, signals.columns.get_loc('signal')] = -1  # Short spread (sell symbol1, buy symbol2)
                signals.iloc[i, signals.columns.get_loc('entry_price')] = price1.iloc[i]
                
                # For short spread
                stop_loss_spread = self.spread_mean + self.stop_zscore * self.spread_std
                take_profit_spread = self.spread_mean  # Revert to mean
                
                price2_at_point = price2.iloc[i]
                stop_loss_price1 = stop_loss_spread + self.hedge_ratio * price2_at_point
                take_profit_price1 = take_profit_spread + self.hedge_ratio * price2_at_point
                
                signals.iloc[i, signals.columns.get_loc('stop_loss')] = stop_loss_price1
                signals.iloc[i, signals.columns.get_loc('take_profit')] = take_profit_price1
            
            # Exit signal: spread has reverted to mean
            elif abs(current_zscore) < self.exit_zscore and i > 0 and abs(zscore.iloc[i-1]) >= self.exit_zscore:
                # Close any existing position
                signals.iloc[i, signals.columns.get_loc('signal')] = 0
        
        return signals
    
    def calculate_position_size(self, signal: Dict, account_balance: float) -> float:
        """
        Calculate position size for pairs trade.
        We'll size based on the first symbol in the pair.
        """
        if signal['signal'] == 0:
            return 0.0
        
        # Use risk management to calculate position size
        from risk.manager import RiskManager
        risk_manager = RiskManager()
        
        # For pairs trade, we need to consider both legs
        # Simplified: size based on symbol1 with stop loss from signal
        stop_loss_price = signal.get('stop_loss', 0)
        entry_price = signal.get('entry_price', 0)
        
        if entry_price > 0 and stop_loss_price > 0:
            position_size = risk_manager.calculate_position_size(
                entry_price, stop_loss_price, account_balance
            )
            return position_size
        
        # Fallback: use fixed percentage of account
        return (account_balance * 0.02) / entry_price if entry_price > 0 else 0.0