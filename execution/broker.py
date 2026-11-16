"""
Paper broker: the single execution gateway of the bot.

Market data comes from the public exchange feed (or the simulated fallback),
but every order is filled locally against a PaperAccount. Nothing here can
place a real order.
"""
from typing import Dict, List, Optional

import config
from utils import setup_logger
from data.fetcher import DataFetcher
from execution.paper import PaperAccount

logger = setup_logger("ExecutionEngine", "execution.log")


class Broker:
    def __init__(self, data_fetcher: DataFetcher = None, account: PaperAccount = None):
        self.data_fetcher = data_fetcher or DataFetcher()
        self.account = account or PaperAccount()

    # --- market data passthrough ------------------------------------------
    def fetch_ticker(self, symbol: str) -> Dict:
        return self.data_fetcher.fetch_ticker(symbol)

    def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict:
        return self.data_fetcher.fetch_order_book(symbol, limit)

    def last_price(self, symbol: str) -> float:
        return float(self.fetch_ticker(symbol).get("last") or 0.0)

    # --- account ------------------------------------------------------------
    def fetch_balance(self) -> Dict:
        return self.account.balances()

    def fetch_positions(self) -> List[Dict]:
        return self.account.list_positions()

    # --- execution ------------------------------------------------------------
    def open_position(self, symbol: str, side: str, size: float, price: float,
                      stop_loss: float = 0.0, take_profit: float = 0.0,
                      meta: Optional[Dict] = None) -> Optional[Dict]:
        fill = self.account.open_position(symbol, side, size, price, stop_loss, take_profit, meta)
        if fill:
            logger.info(f"[PAPER] OPEN {side} {size:.6f} {symbol} @ {fill['price']:.2f}")
        return fill

    def close_position(self, symbol: str, price: float, reason: str = "manual") -> Optional[Dict]:
        fill = self.account.close_position(symbol, price, reason)
        if fill:
            logger.info(f"[PAPER] CLOSE {symbol} @ {fill['price']:.2f} pnl={fill['pnl']:+.2f} ({reason})")
        return fill

    def close_all(self, reason: str = "liquidate") -> List[Dict]:
        fills = []
        for pos in list(self.account.list_positions()):
            price = self.last_price(pos["symbol"]) or pos["mark_price"]
            fill = self.close_position(pos["symbol"], price, reason)
            if fill:
                fills.append(fill)
        return fills


class OrderManager:
    """Thin bookkeeping layer over the broker (kept for API compatibility)."""

    def __init__(self, broker: Broker):
        self.broker = broker
        self.order_history: List[Dict] = []

    def record(self, fill: Dict):
        self.order_history.append(fill)
        self.order_history = self.order_history[-500:]

    def get_order_history(self) -> List[Dict]:
        return list(self.order_history)
