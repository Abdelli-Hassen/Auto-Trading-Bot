#!/usr/bin/env python3
"""
Autonomous Trading System - Main Entry Point
"""

import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List
import config
import pandas as pd

# Import our modules
from data.fetcher import DataFetcher
from data.storage import DataStorage
from execution.broker import Broker, OrderManager
from risk.manager import RiskManager
from strategies.pairs_trading import PairsTradingStrategy
from backtest.engine import BacktestEngine
from monitoring import log_trade, log_signal, log_error, send_alert, get_monitor
from utils import setup_logger

# Initialize design system
try:
    import design_integration
except ImportError:
    pass

# Setup main logger
logger = setup_logger("Main", "main.log")

class TradingBot:
    def __init__(self):
        self.running = False
        self.data_fetcher = DataFetcher(testnet=config.TESTNET)
        self.broker = Broker(testnet=config.TESTNET)
        self.order_manager = OrderManager(self.broker)
        self.storage = DataStorage()
        self.risk_manager = RiskManager(self.storage)
        self.monitor = get_monitor()
        
        # Initialize strategy
        self.strategy = PairsTradingStrategy(pair=("BTC/USDT", "ETH/USDT"))
        
        # For backtesting/demo purposes
        self.backtest_engine = BacktestEngine(initial_capital=config.INITIAL_CAPITAL)
        
        # Performance tracking
        self.daily_stats = {
            'trades': 0,
            'pnl': 0.0,
            'win_rate': 0.0
        }
        
    async def initialize(self):
        """Initialize the trading bot."""
        logger.info("Initializing Autonomous Trading System...")
        
        # Test connections
        try:
            # Test exchange connection
            balance = self.broker.fetch_balance()
            logger.info(f"Exchange connection successful. Balance: {balance}")
            
            # Test data fetch
            ticker = self.data_fetcher.fetch_ticker("BTC/USDT")
            logger.info(f"Data feed working. BTC/USDT: {ticker.get('last', 'N/A')}")
            
            # Send startup alert
            send_alert("Trading Bot Initialized", "INFO")
            
        except Exception as e:
            log_error(f"Initialization failed: {e}", "Initialize")
            send_alert(f"Initialization failed: {e}", "ERROR")
            raise
    
    async def run_backtest_mode(self, start_date: str, end_date: str):
        """Run the bot in backtest mode."""
        logger.info(f"Running backtest from {start_date} to {end_date}")
        
        try:
            # Run backtest
            results = self.backtest_engine.run_backtest(
                self.strategy, 
                "BTC/USDT", 
                start_date, 
                end_date
            )
            
            # Log results
            logger.info(f"Backtest Results:")
            logger.info(f"  Initial Capital: ${results['initial_capital']:,.2f}")
            logger.info(f"  Final Capital: ${results['final_capital']:,.2f}")
            logger.info(f"  Total Return: {results['total_return_percent']:.2%}")
            logger.info(f"  Total Trades: {results['total_trades']}")
            logger.info(f"  Win Rate: {results['win_rate']:.2%}")
            logger.info(f"  Profit Factor: {results['profit_factor']:.2f}")
            logger.info(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
            logger.info(f"  Max Drawdown: {results['max_drawdown']:.2%}")
            
            # Send results alert
            send_alert(
                f"Backtest Complete: Return={results['total_return_percent']:.2%}, "
                f"Trades={results['total_trades']}, Win Rate={results['win_rate']:.2%}",
                "INFO"
            )
            
            return results
            
        except Exception as e:
            log_error(f"Backtest failed: {e}", "Backtest")
            send_alert(f"Backtest failed: {e}", "ERROR")
            raise
    
    async def run_live_mode(self):
        """Run the bot in live trading mode."""
        logger.info("Starting live trading mode...")
        self.running = True
        
        # Send startup alert
        send_alert("Live Trading Started", "INFO")
        
        try:
            while self.running:
                # Main trading loop
                await self._trading_cycle()
                
                # Sleep between cycles (trade on 3-second timeframe)
                await asyncio.sleep(15)  # 3 seconds
                
        except Exception as e:
            log_error(f"Live trading error: {e}", "LiveTrading")
            send_alert(f"Live trading error: {e}", "ERROR")
        finally:
            self.running = False
            send_alert("Live Trading Stopped", "INFO")
    
    async def _trading_cycle(self):
        """Execute one trading cycle."""
        try:
            # Update risk metrics
            risk_metrics = self.risk_manager.get_risk_metrics()
            
            # Check if we should halt trading
            can_trade, reason = self.risk_manager.can_open_new_position(
                "BTC/USDT", 
                []  # In live mode, we'd fetch current positions
            )
            
            if not can_trade:
                logger.warning(f"Trading halted: {reason}")
                # Still sleep and check again later
                return
            
            # Fetch latest data
            btc_data = self.data_fetcher.fetch_ohlcv("BTC/USDT", limit=100)
            eth_data = self.data_fetcher.fetch_ohlcv("ETH/USDT", limit=100)
            
            if btc_data.empty or eth_data.empty:
                logger.warning("Failed to fetch market data")
                return
            
            # Prepare data for strategy (simplified for demo)
            # In reality, we'd need to align timestamps properly
            combined_data = pd.DataFrame({
                'timestamp': btc_data['timestamp'],
                'BTC/USDT_close': btc_data['close'],
                'ETH/USDT_close': eth_data['close']
            })
            
            # For demo, we'll just generate some signals
            # In reality, we'd call strategy.generate_signals()
            # This is a placeholder for the actual strategy logic
            
            # Log that we're alive
            logger.debug(f"Trading cycle completed at {datetime.now()}")
            
        except Exception as e:
            log_error(f"Error in trading cycle: {e}", "TradingCycle")
    
    def stop(self):
        """Stop the trading bot."""
        logger.info("Stopping trading bot...")
        self.running = False
    
    def get_status(self) -> Dict:
        """Get current bot status."""
        return {
            'running': self.running,
            'timestamp': datetime.now().isoformat(),
            'risk_metrics': self.risk_manager.get_risk_metrics(),
            'daily_stats': self.daily_stats
        }

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    if 'bot' in globals():
        bot.stop()
    sys.exit(0)

async def main():
    """Main entry point."""
    global bot
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create bot instance
    bot = TradingBot()
    
    try:
        # Initialize
        await bot.initialize()
        
        # Check if we should run backtest or live mode
        if len(sys.argv) > 1 and sys.argv[1] == "backtest":
            # Run backtest mode
            start_date = sys.argv[2] if len(sys.argv) > 2 else "2024-01-01"
            end_date = sys.argv[3] if len(sys.argv) > 3 else "2024-12-31"
            await bot.run_backtest_mode(start_date, end_date)
        else:
            # Run live mode
            await bot.run_live_mode()
            
    except Exception as e:
        log_error(f"Fatal error in main: {e}", "Main")
        send_alert(f"Fatal error: {e}", "ERROR")
        raise
    finally:
        logger.info("Trading bot shutdown complete")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())