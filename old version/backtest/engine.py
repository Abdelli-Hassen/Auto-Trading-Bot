import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import config
from utils import setup_logger
from data.fetcher import DataFetcher
from data.storage import DataStorage
from data.validator import DataValidator

logger = setup_logger("BacktestEngine", "backtest.log")

class BacktestEngine:
    def __init__(self, initial_capital: float = config.INITIAL_CAPITAL):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}  # symbol -> position info
        self.trades = []     # list of completed trades
        self.equity_curve = []  # list of (timestamp, equity)
        self.data_fetcher = DataFetcher(testnet=True)  # Use testnet for historical data
        self.storage = DataStorage()
        self.validator = DataValidator()
        self.logger = logger
        
    def run_backtest(self, strategy, symbol: str, start_date: str, end_date: str, 
                    timeframe: str = config.TIMEFRAME) -> Dict:
        """
        Run a backtest for a given strategy on historical data.
        Returns a dictionary with performance metrics.
        """
        self.logger.info(f"Starting backtest for {strategy.name} on {symbol} from {start_date} to {end_date}")
        
        # Reset backtest state
        self._reset()
        
        # Fetch historical data
        raw_data = self.data_fetcher.get_historical_data(symbol, start_date, end_date, timeframe)
        if raw_data.empty:
            self.logger.error("No historical data fetched")
            return self._get_results()
        
        # Validate data
        is_valid, errors = self.validator.validate_ohlcv(raw_data, symbol)
        if not is_valid:
            self.logger.warning(f"Data validation issues: {errors}")
            # Continue anyway but log warnings
        
        # Generate signals
        signals_df = strategy.generate_signals(raw_data)
        if signals_df.empty:
            self.logger.warning("No signals generated")
            return self._get_results()
        
        # Ensure signals DataFrame has required columns
        required_columns = ['signal', 'entry_price', 'stop_loss', 'take_profit']
        for col in required_columns:
            if col not in signals_df.columns:
                signals_df[col] = 0.0
        
        # Combine data and signals
        data = raw_data.copy()
        for col in required_columns:
            data[col] = signals_df[col].values
        
        # Iterate through each bar
        for i in range(len(data)):
            current_bar = data.iloc[i]
            timestamp = current_bar['timestamp']
            signal = current_bar['signal']
            entry_price = current_bar['entry_price']
            stop_loss = current_bar['stop_loss']
            take_profit = current_bar['take_profit']
            close_price = current_bar['close']
            
            # Update existing positions
            self._update_positions(timestamp, close_price)
            
            # Check for new signals
            if signal != 0 and len(self.positions) < config.MAX_POSITIONS:
                self._process_signal(timestamp, signal, entry_price, stop_loss, take_profit, close_price)
            
            # Record equity
            equity = self._calculate_equity(close_price)
            self.equity_curve.append((timestamp, equity))
        
        # Close any remaining positions at the end
        if self.positions:
            final_timestamp = data.iloc[-1]['timestamp']
            final_price = data.iloc[-1]['close']
            self._close_all_positions(final_timestamp, final_price, "end_of_backtest")
        
        self.logger.info("Backtest completed")
        return self._get_results()
    
    def _reset(self):
        """Reset backtest state."""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
    
    def _process_signal(self, timestamp: datetime, signal: int, entry_price: float, 
                       stop_loss: float, take_profit: float, current_price: float):
        """Process a trading signal."""
        # Use current price as entry if entry_price is 0 or invalid
        if entry_price <= 0:
            entry_price = current_price
        
        # Calculate stop loss and take profit if not provided
        if stop_loss <= 0:
            from risk.manager import RiskManager
            risk_manager = RiskManager()
            stop_loss = risk_manager.calculate_stop_loss(entry_price, 'long' if signal > 0 else 'short')
        if take_profit <= 0:
            from risk.manager import RiskManager
            risk_manager = RiskManager()
            take_profit = risk_manager.calculate_take_profit(entry_price, 'long' if signal > 0 else 'short', 
                                                            stop_loss_price=stop_loss)
        
        # Calculate position size
        from risk.manager import RiskManager
        risk_manager = RiskManager()
        position_size = risk_manager.calculate_position_size(entry_price, stop_loss, self.capital)
        
        if position_size <= 0:
            self.logger.warning(f"Position size is zero or negative: {position_size}")
            return
        
        # Determine position side
        side = 'long' if signal > 0 else 'short'
        
        # Create position
        position = {
            'symbol': 'SYMBOL',  # Will be set by caller
            'side': side,
            'size': position_size,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'entry_time': timestamp,
            'unrealized_pnl': 0.0
        }
        
        # For simplicity, we'll use a single position per backtest
        # In reality, we'd manage multiple positions
        position_key = f"{side}_{len(self.positions)}"
        self.positions[position_key] = position
        
        self.logger.debug(f"Opened {side} position at {timestamp}: size={position_size:.6f}, entry={entry_price:.2f}")
    
    def _update_positions(self, timestamp: datetime, current_price: float):
        """Update unrealized P&L for open positions."""
        for pos_key, position in self.positions.items():
            if position['side'] == 'long':
                pnl = (current_price - position['entry_price']) * position['size']
            else:  # short
                pnl = (position['entry_price'] - current_price) * position['size']
            
            position['unrealized_pnl'] = pnl
            
            # Check stop loss
            if position['side'] == 'long' and current_price <= position['stop_loss']:
                self._close_position(pos_key, timestamp, current_price, "stop_loss")
                return
            elif position['side'] == 'short' and current_price >= position['stop_loss']:
                self._close_position(pos_key, timestamp, current_price, "stop_loss")
                return
            
            # Check take profit
            if position['side'] == 'long' and current_price >= position['take_profit']:
                self._close_position(pos_key, timestamp, current_price, "take_profit")
                return
            elif position['side'] == 'short' and current_price <= position['take_profit']:
                self._close_position(pos_key, timestamp, current_price, "take_profit")
                return
    
    def _close_position(self, pos_key: str, timestamp: datetime, price: float, reason: str):
        """Close a position and record the trade."""
        if pos_key not in self.positions:
            return
        
        position = self.positions[pos_key]
        
        # Calculate realized P&L
        if position['side'] == 'long':
            pnl = (price - position['entry_price']) * position['size']
        else:  # short
            pnl = (position['entry_price'] - price) * position['size']
        
        # Record trade
        trade = {
            'symbol': position.get('symbol', 'UNKNOWN'),
            'side': position['side'],
            'entry_time': position['entry_time'],
            'exit_time': timestamp,
            'entry_price': position['entry_price'],
            'exit_price': price,
            'size': position['size'],
            'pnl': pnl,
            'pnl_percent': pnl / (position['entry_price'] * position['size']) if position['entry_price'] * position['size'] > 0 else 0,
            'reason': reason
        }
        
        self.trades.append(trade)
        self.capital += pnl
        
        # Remove position
        del self.positions[pos_key]
        
        self.logger.debug(f"Closed position {pos_key} at {timestamp}: {reason}, P&L={pnl:.2f}")
    
    def _close_all_positions(self, timestamp: datetime, price: float, reason: str):
        """Close all open positions."""
        pos_keys = list(self.positions.keys())
        for pos_key in pos_keys:
            self._close_position(pos_key, timestamp, price, reason)
    
    def _calculate_equity(self, current_price: float) -> float:
        """Calculate current equity including unrealized P&L."""
        equity = self.capital
        for position in self.positions.values():
            if position['side'] == 'long':
                unrealized_pnl = (current_price - position['entry_price']) * position['size']
            else:  # short
                unrealized_pnl = (position['entry_price'] - current_price) * position['size']
            equity += unrealized_pnl
        return equity
    
    def _get_results(self) -> Dict:
        """Calculate and return backtest results."""
        if not self.trades:
            return {
                'initial_capital': self.initial_capital,
                'final_capital': self.capital,
                'total_return': 0.0,
                'total_return_percent': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'equity_curve': self.equity_curve,
                'trades': self.trades
            }
        
        # Calculate basic metrics
        total_return = self.capital - self.initial_capital
        total_return_percent = total_return / self.initial_capital if self.initial_capital > 0 else 0
        
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        total_wins = sum(t['pnl'] for t in winning_trades)
        total_losses = abs(sum(t['pnl'] for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0
        
        # Calculate Sharpe ratio
        if self.equity_curve:
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev_equity = self.equity_curve[i-1][1]
                curr_equity = self.equity_curve[i][1]
                if prev_equity > 0:
                    returns.append((curr_equity - prev_equity) / prev_equity)
            
            from utils import calculate_sharpe
            sharpe_ratio = calculate_sharpe(returns)
        else:
            sharpe_ratio = 0.0
        
        # Calculate max drawdown
        if self.equity_curve:
            equity_values = [eq[1] for eq in self.equity_curve]
            from utils import calculate_max_drawdown
            max_drawdown = calculate_max_drawdown(equity_values)
        else:
            max_drawdown = 0.0
        
        results = {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_return': total_return,
            'total_return_percent': total_return_percent,
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'equity_curve': self.equity_curve,
            'trades': self.trades
        }
        
        self.logger.info(f"Backtest results: Return={total_return_percent:.2%}, Trades={len(self.trades)}, Win Rate={win_rate:.2%}")
        return results
