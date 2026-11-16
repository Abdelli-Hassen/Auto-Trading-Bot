"""
Paper-trading account.

Simulates fills locally against live public prices. Supports long and short
positions on a USDT-margined account: cash only moves by realised PnL and fees,
equity = cash + unrealised PnL. No real orders are ever sent anywhere.
"""
import threading
from datetime import datetime
from typing import Dict, List, Optional

import config


class PaperAccount:
    def __init__(self, initial_capital: float = None,
                 fee_rate: float = None, slippage: float = None):
        self.initial_capital = float(initial_capital if initial_capital is not None
                                     else config.INITIAL_CAPITAL)
        self.fee_rate = config.FEE_RATE if fee_rate is None else fee_rate
        self.slippage = config.SLIPPAGE if slippage is None else slippage
        self._lock = threading.RLock()
        self.reset()

    def reset(self):
        with self._lock:
            self.cash = self.initial_capital
            self.positions: Dict[str, Dict] = {}
            self.fees_paid = 0.0
            self.realized_pnl = 0.0

    def _fill_price(self, price: float, side: str) -> float:
        """Buys fill slightly higher, sells slightly lower."""
        return price * (1 + self.slippage) if side == "buy" else price * (1 - self.slippage)

    def open_position(self, symbol: str, side: str, size: float, price: float,
                      stop_loss: float = 0.0, take_profit: float = 0.0,
                      meta: Optional[Dict] = None) -> Optional[Dict]:
        if size <= 0 or price <= 0:
            return None
        with self._lock:
            if symbol in self.positions:
                return None
            order_side = "buy" if side == "long" else "sell"
            fill = self._fill_price(price, order_side)
            fee = fill * size * self.fee_rate
            self.cash -= fee
            self.fees_paid += fee
            self.positions[symbol] = {
                "symbol": symbol, "side": side, "size": size,
                "entry_price": fill, "mark_price": fill,
                "stop_loss": stop_loss, "take_profit": take_profit,
                "entry_fee": fee, "opened_at": datetime.now().isoformat(),
                "meta": meta or {},
            }
            return {"symbol": symbol, "side": order_side, "amount": size,
                    "price": fill, "fee": fee, "pnl": 0.0, "action": "open",
                    "timestamp": datetime.now().isoformat()}

    def close_position(self, symbol: str, price: float, reason: str = "manual") -> Optional[Dict]:
        with self._lock:
            pos = self.positions.get(symbol)
            if not pos or price <= 0:
                return None
            order_side = "sell" if pos["side"] == "long" else "buy"
            fill = self._fill_price(price, order_side)
            direction = 1 if pos["side"] == "long" else -1
            gross = (fill - pos["entry_price"]) * pos["size"] * direction
            fee = fill * pos["size"] * self.fee_rate
            net = gross - fee - pos["entry_fee"]          # round-trip net PnL
            self.cash += gross - fee
            self.fees_paid += fee
            self.realized_pnl += net
            del self.positions[symbol]
            return {"symbol": symbol, "side": order_side, "amount": pos["size"],
                    "price": fill, "fee": fee, "pnl": net, "action": "close",
                    "reason": reason, "entry_price": pos["entry_price"],
                    "position_side": pos["side"],
                    "timestamp": datetime.now().isoformat()}

    def set_signed_size(self, symbol: str, target_units: float, price: float) -> List[Dict]:
        """Resize to a signed position (+long / -short). Flips close first, then open. Returns fills."""
        fills: List[Dict] = []
        with self._lock:
            pos = self.positions.get(symbol)
            cur_side = pos["side"] if pos else None
            want_side = "long" if target_units > 0 else "short" if target_units < 0 else None
            size = abs(target_units)
            if cur_side and want_side != cur_side:                      # close (or flip)
                f = self._resize(symbol, cur_side, 0.0, price)
                if f:
                    fills.append(f)
                cur_side = None
            if want_side:
                f = self._resize(symbol, want_side, size, price)
                if f:
                    fills.append(f)
        return fills

    def set_long_size(self, symbol: str, target_size: float, price: float) -> Optional[Dict]:
        with self._lock:
            return self._resize(symbol, "long", target_size, price)

    def _resize(self, symbol: str, side: str, target_size: float, price: float) -> Optional[Dict]:
        """Grow or shrink a position on one side; fully closing it when target_size is 0."""
        if price <= 0 or target_size < 0:
            return None
        pos = self.positions.get(symbol)
        cur = pos["size"] if pos else 0.0
        delta = target_size - cur
        if abs(delta) < 1e-12:
            return None
        increase_side = "buy" if side == "long" else "sell"          # order side that grows the position
        direction = 1 if side == "long" else -1
        if delta > 0:                                               # grow
            fill = self._fill_price(price, increase_side)
            fee = fill * delta * self.fee_rate
            self.cash -= fee
            self.fees_paid += fee
            if pos is None:
                self.positions[symbol] = {
                    "symbol": symbol, "side": side, "size": delta, "entry_price": fill,
                    "mark_price": price, "stop_loss": 0.0, "take_profit": 0.0, "entry_fee": fee,
                    "realized": 0.0, "opened_at": datetime.now().isoformat(), "meta": {}}
                action = "open"
            else:
                total = cur + delta
                pos["entry_price"] = (pos["entry_price"] * cur + fill * delta) / total
                pos["size"] = total
                pos["entry_fee"] += fee
                pos["mark_price"] = price
                action = "add"
            return {"symbol": symbol, "side": increase_side, "amount": delta, "price": fill, "fee": fee,
                    "pnl": 0.0, "action": action, "closed": False, "position_side": side,
                    "timestamp": datetime.now().isoformat()}
        reduce_side = "sell" if side == "long" else "buy"
        reduce = min(-delta, cur)                                   # shrink / close
        fill = self._fill_price(price, reduce_side)
        frac = reduce / cur
        gross = (fill - pos["entry_price"]) * reduce * direction
        fee = fill * reduce * self.fee_rate
        net = gross - fee - pos["entry_fee"] * frac
        self.cash += gross - fee
        self.fees_paid += fee
        self.realized_pnl += net
        pos["entry_fee"] *= (1 - frac)
        pos["size"] = cur - reduce
        pos["realized"] = pos.get("realized", 0.0) + net
        pos["mark_price"] = price
        closed = pos["size"] <= 1e-12
        trade_pnl = pos["realized"] if closed else 0.0
        if closed:
            del self.positions[symbol]
        return {"symbol": symbol, "side": reduce_side, "amount": reduce, "price": fill, "fee": fee,
                "pnl": net, "action": "close" if closed else "reduce", "closed": closed,
                "trade_pnl": trade_pnl, "position_side": side, "timestamp": datetime.now().isoformat()}

    def mark(self, prices: Dict[str, float]):
        with self._lock:
            for sym, pos in self.positions.items():
                if prices.get(sym):
                    pos["mark_price"] = prices[sym]

    @staticmethod
    def _upnl(pos: Dict) -> float:
        d = 1 if pos["side"] == "long" else -1
        return (pos["mark_price"] - pos["entry_price"]) * pos["size"] * d

    def unrealized_pnl(self) -> float:
        with self._lock:
            return sum(self._upnl(p) for p in self.positions.values())

    def equity(self) -> float:
        with self._lock:
            return self.cash + self.unrealized_pnl()

    def exposure(self) -> float:
        with self._lock:
            return sum(p["size"] * p["mark_price"] for p in self.positions.values())

    def list_positions(self) -> List[Dict]:
        with self._lock:
            out = []
            for p in self.positions.values():
                q = dict(p)
                q["unrealized_pnl"] = self._upnl(p)
                out.append(q)
            return out

    def balances(self) -> Dict:
        """Wallet-style view for the UI: USDT cash plus signed base-asset exposure."""
        with self._lock:
            eq = self.equity()
            result = {"USDT": {"free": round(self.cash, 2), "total": round(eq, 2)}}
            for asset in ("BTC", "ETH", "SOL"):
                result[asset] = {"free": 0.0, "total": 0.0}
            for p in self.positions.values():
                base = p["symbol"].split("/")[0]
                signed = p["size"] if p["side"] == "long" else -p["size"]
                result.setdefault(base, {"free": 0.0, "total": 0.0})
                result[base]["total"] = round(result[base]["total"] + signed, 6)
                result[base]["free"] = round(result[base]["free"] + signed, 6)
            result["total_usdt"] = round(eq, 2)
            return result
