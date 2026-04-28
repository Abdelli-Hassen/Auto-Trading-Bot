import ccxt
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import config
from utils import setup_logger
from data.fetcher import DataFetcher

logger = setup_logger("ExecutionEngine", "execution.log")

class Broker:
    def __init__(self, exchange_id: str = config.EXCHANGE, testnet: bool = config.TESTNET):
        self.exchange_id = exchange_id
        self.exchange = self._create_exchange(testnet)
        self.data_fetcher = DataFetcher(exchange_id, testnet)
        
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
    
    def fetch_ticker(self, symbol: str) -> Dict:
        return self.data_fetcher.fetch_ticker(symbol)
    
    def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict:
        return self.data_fetcher.fetch_order_book(symbol, limit)
    
    def fetch_balance(self) -> Dict:
        return self.data_fetcher.fetch_balance()
    
    def fetch_positions(self) -> List[Dict]:
        return self.data_fetcher.fetch_positions()
    
    def fetch_open_orders(self, symbol: str = None) -> List[Dict]:
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []
    
    def fetch_closed_orders(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        try:
            orders = self.exchange.fetch_closed_orders(symbol, limit=limit)
            return orders
        except Exception as e:
            logger.error(f"Error fetching closed orders: {e}")
            return []
    
    def create_market_order(self, symbol: str, side: str, amount: float, 
                           params: Dict = None) -> Dict:
        try:
            if params is None:
                params = {}
            order = self.exchange.create_market_order(symbol, side, amount, None, params)
            logger.info(f"Created market order: {side} {amount} {symbol}")
            return order
        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            raise
    
    def create_limit_order(self, symbol: str, side: str, amount: float, price: float,
                          params: Dict = None) -> Dict:
        try:
            if params is None:
                params = {}
            order = self.exchange.create_limit_order(symbol, side, amount, price, params)
            logger.info(f"Created limit order: {side} {amount} {symbol} @ {price}")
            return order
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")
            raise
    
    def create_stop_order(self, symbol: str, side: str, amount: float, price: float,
                         params: Dict = None) -> Dict:
        try:
            if params is None:
                params = {}
            order = self.exchange.create_stop_order(symbol, side, amount, price, params)
            logger.info(f"Created stop order: {side} {amount} {symbol} @ {price}")
            return order
        except Exception as e:
            logger.error(f"Error creating stop order: {e}")
            raise
    
    def cancel_order(self, order_id: str, symbol: str = None) -> Dict:
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Cancelled order: {order_id}")
            return result
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            raise
    
    def fetch_order(self, order_id: str, symbol: str = None) -> Dict:
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Error fetching order: {e}")
            raise
    
    def edit_order(self, order_id: str, symbol: str, type: str, side: str,
                   amount: float, price: float, params: Dict = None) -> Dict:
        try:
            if params is None:
                params = {}
            result = self.exchange.edit_order(order_id, symbol, type, side, amount, price, params)
            logger.info(f"Edited order: {order_id}")
            return result
        except Exception as e:
            logger.error(f"Error editing order: {e}")
            raise

class OrderManager:
    def __init__(self, broker: Broker):
        self.broker = broker
        self.pending_orders = {}
        self.filled_orders = {}
        self.order_history = []
        
    async def place_market_order(self, symbol: str, side: str, amount: float,
                                reduce_only: bool = False) -> Optional[Dict]:
        try:
            params = {}
            if reduce_only:
                params['reduceOnly'] = True
                
            order = self.broker.create_market_order(symbol, side, amount, params)
            order_id = order['id']
            
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'type': 'market',
                'status': 'pending',
                'timestamp': datetime.now(),
                'order_obj': order
            }
            
            return order
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return None
    
    async def place_limit_order(self, symbol: str, side: str, amount: float, price: float,
                               reduce_only: bool = False) -> Optional[Dict]:
        try:
            params = {}
            if reduce_only:
                params['reduceOnly'] = True
                
            order = self.broker.create_limit_order(symbol, side, amount, price, params)
            order_id = order['id']
            
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'type': 'limit',
                'status': 'pending',
                'timestamp': datetime.now(),
                'order_obj': order
            }
            
            return order
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return None
    
    async def place_stop_order(self, symbol: str, side: str, amount: float, price: float,
                              stop_price: float = None, reduce_only: bool = False) -> Optional[Dict]:
        try:
            params = {}
            if stop_price:
                params['stopPrice'] = stop_price
            if reduce_only:
                params['reduceOnly'] = True
                
            order = self.broker.create_stop_order(symbol, side, amount, price, params)
            order_id = order['id']
            
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'price': price,
                'stop_price': stop_price,
                'type': 'stop',
                'status': 'pending',
                'timestamp': datetime.now(),
                'order_obj': order
            }
            
            return order
        except Exception as e:
            logger.error(f"Error placing stop order: {e}")
            return None
    
    async def check_order_status(self, order_id: str, symbol: str = None) -> Dict:
        try:
            if order_id not in self.pending_orders:
                logger.warning(f"Order {order_id} not in pending orders")
                return {'status': 'not_found'}
            
            order = self.broker.fetch_order(order_id, symbol)
            status = order['status']
            
            order_info = self.pending_orders[order_id]
            order_info['status'] = status
            order_info['order_obj'] = order
            order_info['filled'] = order.get('filled', 0)
            order_info['remaining'] = order.get('remaining', 0)
            order_info['average'] = order.get('average', 0)
            order_info['cost'] = order.get('cost', 0)
            order_info['fee'] = order.get('fee', {})
            
            if status in ['closed', 'filled']:
                self.filled_orders[order_id] = order_info.copy()
                del self.pending_orders[order_id]
                self.order_history.append(order_info.copy())
                logger.info(f"Order {order_id} filled: {order_info['filled']} @ {order_info.get('average', 0)}")
            elif status in ['canceled', 'cancelled']:
                del self.pending_orders[order_id]
                logger.info(f"Order {order_id} cancelled")
            
            return order_info
        except Exception as e:
            logger.error(f"Error checking order status: {e}")
            return {'status': 'error'}
    
    async def wait_for_order_fill(self, order_id: str, timeout: int = 30) -> Dict:
        start_time = time.time()
        while time.time() - start_time < timeout:
            status_info = await self.check_order_status(order_id)
            status = status_info.get('status', '')
            
            if status in ['closed', 'filled', 'canceled', 'cancelled']:
                return status_info
            
            await asyncio.sleep(1)
        
        logger.warning(f"Order {order_id} not filled within {timeout} seconds")
        return {'status': 'timeout'}
    
    async def cancel_all_orders(self, symbol: str = None):
        try:
            orders = self.broker.fetch_open_orders(symbol)
            for order in orders:
                self.broker.cancel_order(order['id'], symbol)
                logger.info(f"Cancelled order {order['id']} for {symbol}")
        except Exception as e:
            logger.error(f"Error cancelling all orders: {e}")
    
    def get_open_orders(self) -> Dict:
        return self.pending_orders.copy()
    
    def get_filled_orders(self) -> Dict:
        return self.filled_orders.copy()
    
    def get_order_history(self) -> List[Dict]:
        return self.order_history.copy()
