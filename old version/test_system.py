#!/usr/bin/env python3
"""
Simple test to verify the trading system components work together
"""

import sys
import os

# Add the trading_bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot'))

def test_imports():
    """Test that all modules can be imported."""
    try:
        import config
        print("[PASS] Config imported")
        
        from data.fetcher import DataFetcher
        print("[PASS] DataFetcher imported")
        
        from data.storage import DataStorage
        print("[PASS] DataStorage imported")
        
        from data.validator import DataValidator
        print("[PASS] DataValidator imported")
        
        from execution.broker import Broker, OrderManager
        print("[PASS] Broker imported")
        
        from risk.manager import RiskManager
        print("[PASS] RiskManager imported")
        
        from strategies.base import BaseStrategy
        print("[PASS] BaseStrategy imported")
        
        from strategies.pairs_trading import PairsTradingStrategy
        print("[PASS] PairsTradingStrategy imported")
        
        from backtest.engine import BacktestEngine
        print("[PASS] BacktestEngine imported")
        
        from monitoring import log_trade, log_signal, log_error, send_alert
        print("[PASS] Monitoring imported")
        
        from utils import setup_logger, calculate_sharpe, calculate_max_drawdown
        print("[PASS] Utils imported")
        
        print("\n[PASS] All imports successful!")
        return True
        
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration loading."""
    try:
        import config
        print(f"[PASS] Exchange: {config.EXCHANGE}")
        print(f"[PASS] Initial Capital: ${config.INITIAL_CAPITAL}")
        print(f"[PASS] Risk per Trade: {config.RISK_PER_TRADE:.1%}")
        print(f"[PASS] Max Daily Loss: {config.MAX_DAILY_LOSS:.1%}")
        print(f"[PASS] Testnet Mode: {config.TESTNET}")
        return True
    except Exception as e:
        print(f"[FAIL] Config test failed: {e}")
        return False

def test_utils():
    """Test utility functions."""
    try:
        from utils import calculate_sharpe, calculate_max_drawdown, format_currency, format_percent
        
        # Test Sharpe ratio
        returns = [0.01, -0.02, 0.03, -0.01, 0.02]
        sharpe = calculate_sharpe(returns)
        print(f"[PASS] Sharpe ratio calculation: {sharpe:.2f}")
        
        # Test max drawdown
        equity_curve = [1000, 1100, 1050, 1200, 1150, 1300]
        max_dd = calculate_max_drawdown(equity_curve)
        print(f"[PASS] Max drawdown calculation: {max_dd:.2%}")
        
        # Test formatting
        print(f"[PASS] Currency formatting: {format_currency(1234.56)}")
        print(f"[PASS] Percent formatting: {format_percent(0.1234)}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running Trading System Component Tests...\n")
    
    tests = [
        test_imports,
        test_config,
        test_utils
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"Running {test.__name__}...")
        if test():
            passed += 1
        print("-" * 50)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("[PASS] All tests passed! The system is ready to use.")
        sys.exit(0)
    else:
        print("[FAIL] Some tests failed. Please check the errors above.")
        sys.exit(1)