"""
Example usage of the trading system components.
This file demonstrates how to use the various modules together.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the trading_bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot'))

# Import our trading system components
from data.fetcher import DataFetcher
from data.storage import DataStorage
from execution.broker import Broker
from risk.manager import RiskManager
from strategies.pairs_trading import PairsTradingStrategy
from backtest.engine import BacktestEngine
import config

def example_data_operations():
    """Demonstrate data fetching and storage."""
    print("=== Data Operations Example ===")
    
    # Initialize data fetcher (using testnet)
    fetcher = DataFetcher(testnet=True)
    
    # Fetch recent OHLCV data
    print("Fetching BTC/USDT OHLCV data...")
    ohlcv = fetcher.fetch_ohlcv("BTC/USDT", limit=10)
    if not ohlcv.empty:
        print(f"Fetched {len(ohlcv)} candles")
        print(f"Latest close: ${ohlcv['close'].iloc[-1]:.2f}")
    
    # Fetch order book
    print("\nFetching BTC/USDT order book...")
    order_book = fetcher.fetch_order_book("BTC/USDT")
    if order_book.get('bids') and order_book.get('asks'):
        best_bid = order_book['bids'][0][0]
        best_ask = order_book['asks'][0][0]
        spread = (best_ask - best_bid) / best_bid
        print(f"Best bid: ${best_bid:.2f}")
        print(f"Best ask: ${best_ask:.2f}")
        print(f"Spread: {spread:.4f} ({spread*100:.2f}%)")
    
    # Fetch ticker
    print("\nFetching BTC/USDT ticker...")
    ticker = fetcher.fetch_ticker("BTC/USDT")
    print(f"Price: ${ticker.get('last', 0):.2f}")
    print(f"Bid: ${ticker.get('bid', 0):.2f}")
    print(f"Ask: ${ticker.get('ask', 0):.2f}")

def example_risk_management():
    """Demonstrate risk management calculations."""
    print("\n=== Risk Management Example ===")
    
    risk_manager = RiskManager()
    
    # Example: Calculate position size
    entry_price = 50000.0  # $50,000
    stop_loss_price = 49000.0  # $49,000 (2% stop loss)
    account_balance = 10000.0  # $10,000 account
    
    position_size = risk_manager.calculate_position_size(
        entry_price, stop_loss_price, account_balance
    )
    
    print(f"Account Balance: ${account_balance:,.2f}")
    print(f"Entry Price: ${entry_price:,.2f}")
    print(f"Stop Loss: ${stop_loss_price:,.2f}")
    print(f"Risk per Trade: {config.RISK_PER_TRADE:.1%}")
    print(f"Position Size: {position_size:.6f} BTC")
    print(f"Position Value: ${position_size * entry_price:,.2f}")
    print(f"Risk Amount: ${(entry_price - stop_loss_price) * position_size:,.2f}")
    
    # Example: Calculate take profit
    take_profit = risk_manager.calculate_take_profit(
        entry_price, 'long', risk_reward_ratio=2.0, 
        stop_loss_price=stop_loss_price
    )
    print(f"Take Profit (2:1 RR): ${take_profit:,.2f}")
    
    # Example: Risk metrics
    metrics = risk_manager.get_risk_metrics()
    print(f"\nCurrent Risk Metrics:")
    for key, value in metrics.items():
        if isinstance(value, float):
            if 'pnl' in key or 'return' in key or 'drawdown' in key:
                print(f"  {key}: {value:.2%}")
            else:
                print(f"  {key}: ${value:,.2f}")
        else:
            print(f"  {key}: {value}")

def example_strategy():
    """Demonstrate the pairs trading strategy."""
    print("\n=== Strategy Example ===")
    
    # Create strategy instance
    strategy = PairsTradingStrategy(pair=("BTC/USDT", "ETH/USDT"))
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
    np.random.seed(42)  # For reproducible results
    
    # Generate correlated price series (simplified)
    btc_returns = np.random.normal(0.0005, 0.02, 100)  # BTC hourly returns
    eth_returns = 0.8 * btc_returns + np.random.normal(0, 0.01, 100)  # ETH correlated with BTC
    
    btc_prices = 50000 * np.exp(np.cumsum(btc_returns))
    eth_prices = 3000 * np.exp(np.cumsum(eth_returns))
    
    data = pd.DataFrame({
        'timestamp': dates,
        'BTC/USDT_close': btc_prices,
        'ETH/USDT_close': eth_prices
    })
    
    print(f"Generated {len(data)} hourly price bars")
    print(f"BTC price range: ${btc_prices.min():.2f} - ${btc_prices.max():.2f}")
    print(f"ETH price range: ${eth_prices.min():.2f} - ${eth_prices.max():.2f}")
    
    # Generate signals (this would normally use the strategy's generate_signals method)
    # For this example, we'll just show what the strategy parameters are
    print(f"\nStrategy Parameters:")
    print(f"  Pair: {strategy.pair}")
    print(f"  Entry Z-Score: {strategy.entry_zscore}")
    print(f"  Exit Z-Score: {strategy.exit_zscore}")
    print(f"  Stop Z-Score: {strategy.stop_zscore}")
    
    # Show what signals would look like
    signals_df = strategy.generate_signals(data)
    if not signals_df.empty:
        long_signals = (signals_df['signal'] == 1).sum()
        short_signals = (signals_df['signal'] == -1).sum()
        print(f"\nSignals Generated:")
        print(f"  Long signals: {long_signals}")
        print(f"  Short signals: {short_signals}")
        print(f"  No position: {len(signals_df) - long_signals - short_signals}")

def example_backtest():
    """Demonstrate backtesting functionality."""
    print("\n=== Backtesting Example ===")
    
    # Initialize backtest engine
    backtest_engine = BacktestEngine(initial_capital=10000)
    
    # Create strategy
    strategy = PairsTradingStrategy(pair=("BTC/USDT", "ETH/USDT"))
    
    print("Running backtest on synthetic data...")
    # Note: In a real example, we would fetch actual historical data
    # For this demo, we'll skip the actual backtest run since it requires more setup
    
    print("Backtest engine initialized successfully")
    print("To run a real backtest, use:")
    print("  backtest_engine.run_backtest(strategy, 'BTC/USDT', '2024-01-01', '2024-12-31')")

def example_execution():
    """Demonstrate execution capabilities."""
    print("\n=== Execution Example ===")
    
    # Initialize broker (testnet)
    broker = Broker(testnet=True)
    
    print("Broker initialized for Binance testnet")
    print("Available methods:")
    print("  - create_market_order(symbol, side, amount)")
    print("  - create_limit_order(symbol, side, amount, price)")
    print("  - create_stop_order(symbol, side, amount, price)")
    print("  - cancel_order(order_id, symbol)")
    print("  - fetch_order(order_id, symbol)")
    print("  - fetch_balance()")
    print("  - fetch_positions()")
    
    # Show how order manager works
    from execution.broker import OrderManager
    order_manager = OrderManager(broker)
    print("\nOrderManager provides:")
    print("  - Async order placement")
    print("  - Order status tracking")
    print("  - Fill/wait functionality")
    print("  - Order history logging")

def main():
    """Run all examples."""
    print("Autonomous Trading System - Component Examples")
    print("=" * 50)
    
    try:
        example_data_operations()
        example_risk_management()
        example_strategy()
        example_backtest()
        example_execution()
        
        print("\n" + "=" * 50)
        print("SUCCESS: All examples completed successfully!")
        print("\nNext steps:")
        print("1. Review the code in each module")
        print("2. Run: python test_system.py (to verify installation)")
        print("3. Run: python trading_bot/main.py backtest 2024-01-01 2024-12-31 (for backtesting)")
        print("4. Set TESTNET = False in config.py for live trading")
        print("5. Always start with small positions and proper risk management")
        
    except Exception as e:
        print(f"\nERROR: Error running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()