import time
import ccxt
import pandas as pd
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import config
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import setup_logger
from data.synthetic import SyntheticFeed

logger = setup_logger("DataFetcher", "data.log")

class DataFetcher:
    def __init__(self, exchange_id: str = config.EXCHANGE, testnet: bool = config.TESTNET):
        self.exchange_id = exchange_id
        self.testnet = testnet
        self.exchange = self._create_exchange(testnet)
        self.cache = {}
        self._positions_warning_emitted = False
        self.synthetic = SyntheticFeed()
        self._offline_until = 0.0     # monotonic time until which we skip the exchange
        self.data_source = "exchange"  # 'exchange' | 'synthetic'

    # ------------------------------------------------------------ resilience
    def _use_synthetic(self) -> bool:
        if config.FORCE_SYNTHETIC:
            self.data_source = "synthetic"
            return True
        return config.ALLOW_SYNTHETIC_FALLBACK and time.monotonic() < self._offline_until

    def _blocked(self) -> bool:
        """Offline with no fallback: skip the exchange for a few seconds instead of hammering it."""
        return (not config.ALLOW_SYNTHETIC_FALLBACK and not config.FORCE_SYNTHETIC
                and self.data_source == "offline" and time.monotonic() < self._offline_until)

    def feed_ok(self) -> bool:
        return self.data_source != "offline"

    def _mark_offline(self, err: Exception):
        if not config.ALLOW_SYNTHETIC_FALLBACK:
            if self.data_source != "offline":
                logger.error(f"Exchange unreachable ({str(err)[:80]}); price feed OFFLINE - trading is paused")
            self.data_source = "offline"
            self._offline_until = time.monotonic() + 15
            return
        if self.data_source != "synthetic":
            logger.warning(f"Exchange unreachable ({str(err)[:80]}); using simulated price feed")
        self.data_source = "synthetic"
        self._offline_until = time.monotonic() + 60   # retry the exchange in a minute

    def _mark_online(self):
        if self.data_source != "exchange":
            logger.info("Exchange reachable again; using live prices")
        self.data_source = "exchange"
        
    def _create_exchange(self, testnet: bool) -> ccxt.Exchange:
        exchange_class = getattr(ccxt, self.exchange_id)
        
        params = {"enableRateLimit": True, "timeout": 6000,
                  "options": {"adjustForTimeDifference": False}}
        # Paper trading uses public market data only: never attach API keys.
        return exchange_class(params)
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = config.TIMEFRAME, 
                     limit: int = 100, since: Optional[int] = None) -> pd.DataFrame:
        if self._blocked():
            return pd.DataFrame()
        if not self._use_synthetic():
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit, since=since)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['symbol'] = symbol
                self._mark_online()
                return df
            except Exception as e:
                logger.error(f"Error fetching OHLCV for {symbol}: {e}")
                self._mark_offline(e)
        if config.ALLOW_SYNTHETIC_FALLBACK:
            df = self.synthetic.ohlcv(symbol, timeframe, limit)
            df['symbol'] = symbol
            return df
        return pd.DataFrame()
    
    def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict:
        if self._blocked():
            return {'bids': [], 'asks': []}
        if not self._use_synthetic():
            try:
                return self.exchange.fetch_order_book(symbol, limit)
            except Exception as e:
                logger.error(f"Error fetching order book for {symbol}: {e}")
                self._mark_offline(e)
        if config.ALLOW_SYNTHETIC_FALLBACK:
            return self.synthetic.order_book(symbol, limit)
        return {'bids': [], 'asks': []}
    
    def fetch_ticker(self, symbol: str) -> Dict:
        if self._blocked():
            return {}
        if not self._use_synthetic():
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                self._mark_online()
                return ticker
            except Exception as e:
                logger.error(f"Error fetching ticker for {symbol}: {e}")
                self._mark_offline(e)
        if config.ALLOW_SYNTHETIC_FALLBACK:
            return self.synthetic.ticker(symbol)
        return {}
    
    def fetch_balance(self) -> Dict:
        try:
            balance = self.exchange.fetch_balance()
            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return {}
    
    def fetch_positions(self) -> List[Dict]:
        try:
            positions = self.exchange.fetch_positions()
            return [p for p in positions if p.get('contracts', 0) > 0]
        except Exception as e:
            error_text = str(e).lower()
            # Binance removed futures sandbox/testnet support in this path.
            # Avoid log flooding when running testnet/desktop refresh loops.
            if (
                self.exchange_id == "binance"
                and self.testnet
                and ("sandbox mode is not supported for futures anymore" in error_text)
            ):
                if not self._positions_warning_emitted:
                    logger.warning(
                        "Binance testnet futures positions endpoint unavailable; "
                        "returning empty positions list."
                    )
                    self._positions_warning_emitted = True
                return []
            logger.error(f"Error fetching positions: {e}")
            return []
    
    def fetch_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        try:
            trades = self.exchange.fetch_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            logger.error(f"Error fetching trades for {symbol}: {e}")
            return []
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str,
                           timeframe: str = config.TIMEFRAME) -> pd.DataFrame:
        all_data = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        requests_left = 25   # hard cap so a bad range can never loop forever
        while current_date < end and requests_left > 0:
            requests_left -= 1
            since = int(current_date.timestamp() * 1000)
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                if not ohlcv:
                    break
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                all_data.append(df)
                
                last_time = df['timestamp'].iloc[-1]
                current_date = last_time + timedelta(minutes=1)
                
                if last_time >= end:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching historical data: {e}")
                self._mark_offline(e)
                break
        
        if not all_data and config.ALLOW_SYNTHETIC_FALLBACK:
            return self.synthetic.ohlcv(symbol, timeframe, 1000)
        if all_data:
            df = pd.concat(all_data, ignore_index=True)
            df = df.drop_duplicates('timestamp').sort_values('timestamp').reset_index(drop=True)
            return df[df['timestamp'] <= end + timedelta(days=1)].reset_index(drop=True)
        return pd.DataFrame()
    
    def get_spread(self, symbol: str) -> float:
        order_book = self.fetch_order_book(symbol)
        if order_book.get('bids') and order_book.get('asks'):
            best_bid = order_book['bids'][0][0]
            best_ask = order_book['asks'][0][0]
            return (best_ask - best_bid) / best_bid
        return 0.0
    
    def get_liquidity(self, symbol: str, depth: int = 10) -> Dict:
        order_book = self.fetch_order_book(symbol, depth)
        bid_volume = sum(bid[1] for bid in order_book.get('bids', []))
        ask_volume = sum(ask[1] for ask in order_book.get('asks', []))
        return {'bid_volume': bid_volume, 'ask_volume': ask_volume, 'total': bid_volume + ask_volume}
    
    async def stream_data(self, symbols: List[str], callback):
        while True:
            try:
                for symbol in symbols:
                    ticker = self.fetch_ticker(symbol)
                    order_book = self.fetch_order_book(symbol)
                    await callback(symbol, ticker, order_book)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in data stream: {e}")
                await asyncio.sleep(5)