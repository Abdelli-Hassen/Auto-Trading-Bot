#!/usr/bin/env python3
"""
Generate realistic test data and run a backtest to validate the system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the trading_bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot'))

from strategies.pairs_trading import PairsTradingStrategy
from backtest.engine import BacktestEngine

def generate_test_data(days=90):
    """Generate realistic price data for BTC and ETH with some cointegration."""
    print(f"Generating {days} days of test data...")
    
    # Generate hourly timestamps
    hours = days * 24
    timestamps = pd.date_range(
        start='2024-01-01', 
        periods=hours, 
        freq='1h'
    )
    
    # Generate correlated random walks for BTC and ETH
    np.random.seed(42)  # For reproducible results
    
    # BTC price: start at $40k, with some drift and volatility
    btc_returns = np.random.normal(0.0002, 0.02, hours)  # ~0.02% hourly return, 2% volatility
    btc_prices = 40000 * np.exp(np.cumsum(btc_returns))
    
    # ETH price: correlated with BTC but with its own volatility
    # ETH typically moves about 1.5-2x as much as BTC
    eth_returns = 0.8 * btc_returns + np.random.normal(0.0001, 0.03, hours)
    eth_prices = 2500 * np.exp(np.cumsum(eth_returns))
    
    # Create DataFrame
    data = pd.DataFrame({
        'timestamp': timestamps,
        'BTC/USDT_close': btc_prices,
        'ETH/USDT_close': eth_prices
    })
    
    print(f"Generated data shape: {data.shape}")
    print(f"BTC price range: ${btc_prices.min():.2f} - ${btc_prices.max():.2f}")
    print(f"ETH price range: ${eth_prices.min():.2f} - ${eth_prices.max():.2f}")
    
    return data

def run_proper_backtest():
    """Run a proper backtest with generated data."""
    print("=" * 60)
    print("RUNNING PROPER BACKTEST")
    print("=" * 60)
    
    # Generate test data
    test_data = generate_test_data(days=60)  # 2 months of hourly data
    
    # Save to CSV for inspection if needed
    test_data.to_csv('test_data.csv', index=False)
    print("Test data saved to test_data.csv")
    
    # Initialize backtest engine
    backtest_engine = BacktestEngine(initial_capital=10000)
    
    # Create strategy
    strategy = PairsTradingStrategy(pair=("BTC/USDT", "ETH/USDT"))
    
    print(f"\nStrategy: {strategy.name}")
    print(f"Pair: {strategy.pair}")
    print(f"Entry Z-Score: {strategy.entry_zscore}")
    print(f"Exit Z-Score: {strategy.exit_zscore}")
    print(f"Stop Z-Score: {strategy.stop_zscore}")
    
    # Run backtest using our custom data
    # We need to modify the backtest engine to accept our data directly
    # For now, let's create a simple version
    
    from data.storage import DataStorage
    from data.validator import DataValidator
    
    storage = DataStorage()
    validator = DataValidator()
    
    # Manually run the backtest logic
    print("\nRunning backtest logic...")
    
    # Reset backtest state
    backtest_engine._reset()
    
    # Use our generated data
    raw_data = test_data.copy()
    
    # Validate data
    is_valid, errors = validator.validate_ohlcv(raw_data, "BTC/USDT")
    if not is_valid:
        print(f"Warning: Data validation issues: {errors}")
    
    # Generate signals
    signals_df = strategy.generate_signals(raw_data)
    if signals_df.empty:
        print("Error: No signals generated")
        return
    
    print(f"Signals generated: {len(signals_df)} rows")
    long_signals = (signals_df['signal'] == 1).sum()
    short_signals = (signals_df['signal'] == -1).sum()
    print(f"Long signals: {long_signals}, Short signals: {short_signals}")
    
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
    print("Processing trading signals...")
    for i in range(len(data)):
        current_bar = data.iloc[i]
        timestamp = current_bar['timestamp']
        signal = current_bar['signal']
        entry_price = current_bar['entry_price']
        stop_loss = current_bar['stop_loss']
        take_profit = current_bar['take_profit']
        close_price = current_bar['BTC/USDT_close']  # Use BTC as reference
        
        # Update existing positions
        backtest_engine._update_positions(timestamp, close_price)
        
        # Check for new signals
        if signal != 0 and len(backtest_engine.positions) < 3:  # MAX_POSITIONS
            backtest_engine._process_signal(timestamp, signal, entry_price, stop_loss, take_profit, close_price)
        
        # Record equity
        equity = backtest_engine._calculate_equity(close_price)
        backtest_engine.equity_curve.append((timestamp, equity))
        
        # Progress indicator
        if i % 1000 == 0 and i > 0:
            print(f"  Processed {i}/{len(data)} bars...")
    
    # Close any remaining positions at the end
    if backtest_engine.positions:
        final_timestamp = data.iloc[-1]['timestamp']
        final_price = data.iloc[-1]['BTC/USDT_close']
        backtest_engine._close_all_positions(final_timestamp, final_price, "end_of_backtest")
    
    # Get results
    results = backtest_engine._get_results()
    
    # Print results
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"Initial Capital:     ${results['initial_capital']:,.2f}")
    print(f"Final Capital:       ${results['final_capital']:,.2f}")
    print(f"Total Return:        {results['total_return_percent']:.2%}")
    print(f"Total Trades:        {results['total_trades']}")
    print(f"Winning Trades:      {results['winning_trades']}")
    print(f"Losing Trades:       {results['losing_trades']}")
    print(f"Win Rate:            {results['win_rate']:.2%}")
    print(f"Profit Factor:       {results['profit_factor']:.2f}")
    print(f"Sharpe Ratio:        {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown:        {results['max_drawdown']:.2%}")
    
    if results['trades']:
        print(f"\nTrade Analysis:")
        pnls = [t['pnl'] for t in results['trades']]
        print(f"  Average P&L:       ${np.mean(pnls):.2f}")
        print(f"  Median P&L:        ${np.median(pnls):.2f}")
        print(f"  Best Trade:        ${max(pnls):.2f}")
        print(f"  Worst Trade:       ${min(pnls):.2f}")
        print(f"  Std Dev P&L:       ${np.std(pnls):.2f}")
    
    # Save results
    results_df = pd.DataFrame(results['trades'])
    if not results_df.empty:
        results_df.to_csv('backtest_trades.csv', index=False)
        print(f"\nDetailed trades saved to backtest_trades.csv")
    
    equity_df = pd.DataFrame(results['equity_curve'], columns=['timestamp', 'equity'])
    equity_df.to_csv('backtest_equity.csv', index=False)
    print(f"Equity curve saved to backtest_equity.csv")
    
    return results

if __name__ == "__main__":
    try:
        results = run_proper_backtest()
        print("\n✅ Backtest completed successfully!")
    except Exception as e:
        print(f"\n❌ Error running backtest: {e}")
        import traceback
        traceback.print_exc()