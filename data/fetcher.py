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

logger = setup_logger("DataFetcher", "data.log")

class DataFetcher:
    def __init__(self, exchange_id: str = config.EXCHANGE, testnet: bool = config.TESTNET):
        self.exchange_id = exchange_id
        self.testnet = testnet
        self.exchange = self._create_exchange(testnet)
        self.cache = {}
        self._positions_warning_emitted = False
        
    def _create_exchange(self, testnet: bool) -> ccxt.Exchange:
        exchange_class = getattr(ccxt, self.exchange_id)
        
        params = {"enableRateLimit": True}
        if testnet and self.exchange_id == "binance":
            params["testnet"] = True
            
        if config.API_KEY and config.API_SECRET:
            exchange = exchange_class({
                'apiKey': config.API_KEY,
                'secret': config.API_SECRET,
                **params
            })
        else:
            exchange = exchange_class(params)
            
        return exchange
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = config.TIMEFRAME, 
                     limit: int = 100, since: Optional[int] = None) -> pd.DataFrame:
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit, since=since)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            return df
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict:
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)
            return order_book
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return {'bids': [], 'asks': []}
    
    def fetch_ticker(self, symbol: str) -> Dict:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
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
        
        while current_date < end:
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
                break
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
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