#!/usr/bin/env python3
"""
Autonomous paper-trading system - main entry point.

Run `python main.py` for the live paper loop or
`python main.py backtest 2024-01-01 2024-03-01` for a backtest.

All orders are simulated locally (see execution/paper.py). No API keys are used
and no real money is ever at risk.
"""
import asyncio
import signal
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

import config
from backtest.engine import BacktestEngine
from data.fetcher import DataFetcher
from data.storage import DataStorage
from execution.broker import Broker, OrderManager
from execution.paper import PaperAccount
from monitoring import get_monitor, log_error, log_signal, send_alert
from risk.manager import RiskManager
from strategies.pairs_trading import PairsTradingStrategy
from strategies.trend_momentum import TrendMomentumStrategy, WARMUP_BARS
from utils import setup_logger
from utils import settings as cfgmod

logger = setup_logger("Main", "main.log")

STATE_KEY = "paper_account"
BARS = 120   # 1m candles per cycle used for the spread statistics


class TradingBot:
    def __init__(self, storage: DataStorage = None, data_fetcher: DataFetcher = None):
        self.running = False
        self.storage = storage or DataStorage()
        self.data_fetcher = data_fetcher or DataFetcher()
        self.account = PaperAccount(config.INITIAL_CAPITAL)
        self.broker = Broker(self.data_fetcher, self.account)
        self.order_manager = OrderManager(self.broker)
        self.risk_manager = RiskManager(self.storage, equity_provider=self.account.equity)
        self.monitor = get_monitor()
        self.strategy = PairsTradingStrategy(pair=("BTC/USDT", "ETH/USDT"))
        self.portfolio_strategies = {"trend_momentum": TrendMomentumStrategy(),
                                     "trend_momentum_ls": TrendMomentumStrategy(allow_shorts=True)}
        self.strategy_id = "pairs" if config.STRATEGY == "pairs" else "trend_momentum"
        self.scan: Dict = {}
        self.analysis_at: Optional[str] = None
        self._analysis_bar = None
        self.backtests: Dict[str, Dict] = {}
        self.settings: Dict = {"strategy": self.strategy_id, "params": {}}
        self.target_weights: Dict[str, float] = {}
        self._last_bar = None          # timestamp of the last 4h bar we rebalanced on
        self.backtest_engine = BacktestEngine(config.INITIAL_CAPITAL, self.data_fetcher)

        self.pair_trades: List[Dict] = []        # closed pair trades (newest last)
        self.recent_signals: List[Dict] = []
        self.pair_stats: Dict = {"ready": False, "z": 0.0}
        self.current_prediction = {"action": "NEUTRAL", "confidence": 0.5, "sentiment": "NEUTRAL"}
        self.last_cycle: Optional[str] = None
        self.started_at: Optional[str] = None
        self._restore_state()
        self._load_settings()

    @property
    def portfolio_strategy(self) -> TrendMomentumStrategy:
        return self.portfolio_strategies.get(self.strategy_id, self.portfolio_strategies["trend_momentum"])

    @property
    def portfolio_mode(self) -> bool:
        return self.strategy_id != "pairs"

    @portfolio_mode.setter
    def portfolio_mode(self, value: bool):
        self.strategy_id = "trend_momentum" if value else "pairs"

    # ------------------------------------------------------------ persistence
    def _save_state(self):
        a = self.account
        self.storage.save_state(STATE_KEY, {
            "cash": a.cash, "positions": a.positions, "fees_paid": a.fees_paid,
            "realized_pnl": a.realized_pnl, "pair_trades": self.pair_trades[-500:],
            "recent_signals": self.recent_signals[:10],
        })

    def _restore_state(self):
        try:
            st = self.storage.load_state(STATE_KEY)
        except Exception as e:  # corrupt/missing db must never block startup
            logger.warning(f"Could not restore state: {e}")
            return
        if not st:
            return
        a = self.account
        a.cash = float(st.get("cash", a.cash))
        a.positions = st.get("positions", {})
        a.fees_paid = float(st.get("fees_paid", 0.0))
        a.realized_pnl = float(st.get("realized_pnl", 0.0))
        self.pair_trades = st.get("pair_trades", [])
        self.recent_signals = st.get("recent_signals", [])
        logger.info(f"Restored paper account: equity={a.equity():,.2f}, positions={len(a.positions)}")

    # ---------------------------------------------------------------- lifecycle
    async def initialize(self):
        logger.info("Initializing paper trading system (no real money, public data only)...")
        try:
            ticker = await asyncio.to_thread(self.data_fetcher.fetch_ticker, "BTC/USDT")
            logger.info(f"Data feed [{self.data_fetcher.data_source}] BTC/USDT: {ticker.get('last', 'N/A')}")
        except Exception as e:
            log_error(f"Data feed check failed: {e}", "Initialize")
        if self.storage.get_stats().get('equity_records', 0) == 0:
            self.storage.store_equity(self.account.equity(), self.account.cash)
        send_alert("Paper trading system initialized", "INFO")

    def stop(self):
        logger.info("Stopping trading bot...")
        self.running = False

    def reset(self):
        """Wipe the paper account and all history back to the initial capital."""
        if self.running:
            raise RuntimeError("Stop the bot before resetting")
        self.settings.pop("flows", None)
        self.account.initial_capital = float(config.INITIAL_CAPITAL)
        self.account.reset()
        self.storage.reset_all()
        self.risk_manager.reset_all()
        self.pair_trades, self.recent_signals = [], []
        self.pair_stats = {"ready": False, "z": 0.0}
        self.target_weights, self._last_bar = {}, None
        self.current_prediction = {"action": "NEUTRAL", "confidence": 0.5, "sentiment": "NEUTRAL"}
        self.storage.store_equity(self.account.equity(), self.account.cash)
        self._save_state()
        send_alert("Paper account reset", "WARNING")

    # --------------------------------------------------------------- backtest
    async def run_backtest_mode(self, start_date: str, end_date: str, timeframe: str = "1h") -> Dict:
        logger.info(f"Running backtest from {start_date} to {end_date}")
        try:
            if self.portfolio_mode:
                results = await asyncio.to_thread(
                    self.backtest_engine.run_portfolio, self.portfolio_strategy, start_date, end_date)
            else:
                results = await asyncio.to_thread(
                    self.backtest_engine.run_backtest, self.strategy, start_date, end_date, timeframe)
            send_alert(f"Backtest complete: return={results['total_return_percent']:.2%}, "
                       f"trades={results['total_trades']}, win rate={results['win_rate']:.0%}", "INFO")
            return results
        except Exception as e:
            log_error(f"Backtest failed: {e}", "Backtest")
            send_alert(f"Backtest failed: {e}", "ERROR")
            raise

    # -------------------------------------------------------------------- live
    async def run_live_mode(self):
        if self.running:
            return
        logger.info("Starting live paper-trading loop...")
        self.running = True
        self.started_at = datetime.now().isoformat()
        self.risk_manager.halted_reason = None
        send_alert("Paper trading started", "INFO")
        try:
            while self.running:
                await self._trading_cycle()
                # sleep in small steps so Stop is responsive
                for _ in range(config.CYCLE_SECONDS * 2):
                    if not self.running:
                        break
                    await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log_error(f"Live trading error: {e}", "LiveTrading")
            send_alert(f"Live trading error: {e}", "ERROR")
        finally:
            self.running = False
            self._save_state()
            send_alert("Paper trading stopped", "INFO")

    def _spread_position(self) -> Optional[str]:
        pos = self.account.positions.get(self.strategy.symbol1)
        return pos["side"] if pos else None


    # ---------------------------------------------------------------- settings
    def _load_settings(self):
        try:
            saved = self.storage.load_state("settings") or {}
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
            return
        self.settings.update({k: v for k, v in saved.items() if k in ("strategy", "params", "risk", "execution", "flows")})
        self.risk_manager.peak_adjust = float(self.settings.get("flows", {}).get("peak_adjust", 0.0))
        if "initial_capital" in self.settings.get("execution", {}):
            self.account.initial_capital = float(self.settings["execution"]["initial_capital"])
        cfgmod.apply_global(self.settings.get("risk"), self.settings.get("execution"))
        if self.settings.get("strategy") in cfgmod.STRATEGY_PARAMS:
            self.strategy_id = self.settings["strategy"]
        self._apply_strategy_params(self.strategy_id)
        self.account.fee_rate, self.account.slippage = config.FEE_RATE, config.SLIPPAGE

    def _persist_settings(self):
        self.settings["strategy"] = self.strategy_id
        self.storage.save_state("settings", self.settings)

    def _apply_strategy_params(self, sid: str):
        params = {**{k: v["default"] for k, v in cfgmod.STRATEGY_PARAMS[sid].items()},
                  **self.settings.get("params", {}).get(sid, {})}
        for key, val in params.items():
            attr = cfgmod.PARAM_TARGETS.get(key)
            if attr:
                setattr(config, attr, val)
        if sid in self.portfolio_strategies:
            self.portfolio_strategies[sid].target_vol = params["target_vol"]
        else:
            self.strategy.entry_zscore = params["entry_threshold"]
            self.strategy.exit_zscore = params["exit_threshold"]
            self.strategy.stop_zscore = params["stop_threshold"]
        return params

    def get_params(self, sid: str) -> Dict:
        defs = cfgmod.STRATEGY_PARAMS[sid]
        saved = self.settings.get("params", {}).get(sid, {})
        return {k: saved.get(k, d["default"]) for k, d in defs.items()}

    def update_params(self, sid: str, values: Dict) -> Dict:
        if sid not in cfgmod.STRATEGY_PARAMS:
            raise ValueError("Unknown strategy")
        defs = cfgmod.STRATEGY_PARAMS[sid]
        clean = {}
        for k, v in (values or {}).items():
            if k not in defs:
                raise ValueError(f"Unknown parameter: {k}")
            d = defs[k]
            try:
                num = float(v)
            except (TypeError, ValueError):
                raise ValueError(f"{d['label']}: not a number")
            if not (d["min"] <= num <= d["max"]):
                raise ValueError(f"{d['label']} must be between {d['min']} and {d['max']}")
            clean[k] = num
        self.settings.setdefault("params", {}).setdefault(sid, {}).update(clean)
        if sid == self.strategy_id:
            self._apply_strategy_params(sid)
            self._last_bar = None          # re-evaluate targets with the new parameters
        self._persist_settings()
        send_alert(f"Parameters updated for {sid.replace('_', ' ')}", "INFO")
        return self.get_params(sid)

    def update_settings(self, risk: Dict = None, execution: Dict = None) -> Dict:
        risk = cfgmod.validate(cfgmod.RISK_SCHEMA, risk or {})
        execution = cfgmod.validate(cfgmod.EXEC_SCHEMA, execution or {})
        cfgmod.apply_global(risk, execution)
        self.settings.setdefault("risk", {}).update(risk)
        self.settings.setdefault("execution", {}).update(execution)
        self.account.fee_rate, self.account.slippage = config.FEE_RATE, config.SLIPPAGE
        if any(k in execution for k in ("trade_budget_pct", "trade_budget_usd", "trade_size_usd")):
            self._last_bar = None                                      # re-size positions to the new budget
        self._persist_settings()
        send_alert("Settings saved", "INFO")
        return cfgmod.current_values()

    def select_strategy(self, sid: str):
        if sid not in cfgmod.STRATEGY_PARAMS:
            raise ValueError("Unknown strategy")
        if sid == self.strategy_id:
            return
        if self.running:
            raise RuntimeError("Stop the bot before switching strategy")
        if self.account.positions:
            raise RuntimeError("Close open positions (Emergency Liquidate) before switching strategy")
        self.strategy_id = sid
        self._apply_strategy_params(sid)
        self.target_weights, self._last_bar, self._analysis_bar, self.scan = {}, None, None, {}
        self._bar_checked = None          # force a fresh analysis for the new strategy
        self.pair_stats = {"ready": False, "z": 0.0}
        self._persist_settings()
        send_alert(f"Strategy switched to {sid.replace('_', ' ')}", "INFO")

    # ---------------------------------------------------------------- analysis
    async def refresh_analysis(self):
        """Download market data and recompute the strategy's current view (no trading)."""
        try:
            if self.portfolio_mode:
                strat = self.portfolio_strategy
                frames = await asyncio.gather(
                    *(asyncio.to_thread(self.data_fetcher.fetch_ohlcv, s, strat.timeframe, 1000)
                      for s in strat.symbols))
                closes = {s.split("/")[0]: df.set_index("timestamp")["close"].iloc[:-1]
                          for s, df in zip(strat.symbols, frames) if not df.empty}
                P = pd.DataFrame(closes).dropna()
                if len(closes) < len(strat.symbols) or len(P) < WARMUP_BARS:
                    logger.warning(f"Not enough market history ({len(P)} aligned bars)")
                    return False
                new_w = strat.target_weights(P)
                self.scan = {**strat.explain(P), "kind": "portfolio"}
                changed = {k for k, v in new_w.items() if abs(v - self.target_weights.get(k, 0.0)) > 0.01}
                if changed and self.target_weights:
                    held = ", ".join(f"{k.split('/')[0]} {'short ' if v < 0 else ''}{abs(v):.0%}" for k, v in new_w.items() if v) or "cash"
                    send_alert(f"Signal update: target is now {held}", "INFO")
                self.target_weights = new_w
                self._analysis_bar = P.index[-1]
            else:
                s1, s2 = self.strategy.pair
                d1, d2 = await asyncio.gather(
                    asyncio.to_thread(self.data_fetcher.fetch_ohlcv, s1, "1m", BARS),
                    asyncio.to_thread(self.data_fetcher.fetch_ohlcv, s2, "1m", BARS))
                if d1.empty or d2.empty:
                    return False
                df = pd.merge(d1[["timestamp", "close"]], d2[["timestamp", "close"]],
                              on="timestamp", suffixes=("_1", "_2")).dropna()
                self.pair_stats = self.strategy.analyze(df["close_1"], df["close_2"])
                self._update_prediction(self.pair_stats)
                self.scan = {"kind": "pair", "symbols": [s1, s2], **self.pair_stats}
            self._bar_checked = datetime.now()
            self.analysis_at = datetime.now().isoformat()
            return True
        except Exception as e:
            log_error(f"Analysis failed: {e}", "Analysis")
            return False

    @staticmethod
    def next_bar_seconds(bar_seconds: int = 14400) -> int:
        now = int(time.time())
        return bar_seconds - (now % bar_seconds)

    def describe(self) -> str:
        """One-sentence plain-English description of what the bot is doing / thinking."""
        if self.risk_manager.halted_reason:
            return f"Entries blocked: {self.risk_manager.halted_reason}."
        if self.portfolio_mode:
            if not self.scan or self.scan.get("kind") != "portfolio":
                return "Analysing the market (downloading 4h history for 8 coins)..."
            rows = self.scan["rows"]
            up = sum(1 for r in rows if r["trend_up"])
            held = [f"{r['symbol'].split('/')[0]} {'short ' if r['target'] < 0 else ''}{abs(r['target']):.0%}"
                    for r in rows if r["target"] != 0]
            regime = "BTC is in an uptrend" if self.scan["btc_regime_up"] else "BTC is below its long-term trend"
            if held:
                return (f"Targeting {sum(abs(r['target']) for r in rows):.0%} exposure: {', '.join(held)} "
                        f"({up}/8 coins in uptrend, {regime}).")
            return (f"Holding cash: only {up}/8 coins are above their trend and none passes the breakout/momentum "
                    f"filters ({regime}). Waiting for a trend to start.")
        z = self.pair_stats.get("z", 0.0) if self.pair_stats.get("ready") else None
        if z is None:
            return "Analysing BTC/ETH spread..."
        pos = self._spread_position()
        if pos:
            return f"In a {pos} spread position. Spread z-score {z:+.2f}; exit near ±{config.EXIT_THRESHOLD}."
        return f"Watching BTC/ETH spread: z-score {z:+.2f}, waiting for ±{config.ENTRY_THRESHOLD} to enter."

    # ------------------------------------------------------------ per-strategy
    def strategy_stats(self, sid: str) -> Dict:
        trades = [t for t in self.pair_trades if t.get("strategy", "pairs" if sid == "pairs" else "trend_momentum") == sid]
        n = len(trades)
        wins = sum(1 for t in trades if t["pnl"] > 0)
        pnls = [t["pnl"] for t in trades]
        unreal = self.account.unrealized_pnl() if sid == self.strategy_id else 0.0
        return {
            "trades": n,
            "win_rate": (wins / n) if n else None,
            "realized_pnl": sum(pnls),
            "unrealized_pnl": unreal,
            "best": max(pnls) if pnls else None,
            "worst": min(pnls) if pnls else None,
        }

    async def run_strategy_backtest(self, sid: str) -> Dict:
        """Backtest on recent real history; result is cached for the Strategies page."""
        end = datetime.now()
        if sid in self.portfolio_strategies:
            start = end - pd.Timedelta(days=3 * 365)
            res = await asyncio.to_thread(self.backtest_engine.run_portfolio, self.portfolio_strategies[sid],
                                          start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            label = "3 years, 4h bars"
        else:
            start = end - pd.Timedelta(days=45)
            res = await asyncio.to_thread(self.backtest_engine.run_backtest, self.strategy,
                                          start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), "1h")
            label = "45 days, 1h bars"
        out = {k: v for k, v in res.items() if k not in ("equity_curve", "trades")}
        curve = res.get("equity_curve", [])
        step = max(len(curve) // 120, 1)
        out["curve"] = [round(v, 2) for _, v in curve[::step]]
        out.update({"label": label, "ran_at": datetime.now().isoformat(), "params": self.get_params(sid)})
        self.backtests[sid] = out
        return out

    # ------------------------------------------------------ portfolio strategy
    async def _portfolio_cycle(self):
        """Trend + momentum portfolio: rebalance toward target weights on each new 4h bar."""
        strat = self.portfolio_strategy
        try:
            # cheap mark-to-market every cycle
            tickers = await asyncio.gather(
                *(asyncio.to_thread(self.data_fetcher.fetch_ticker, s) for s in strat.symbols))
            prices = {s: float(t.get("last") or 0) for s, t in zip(strat.symbols, tickers) if t}
            prices = {s: p for s, p in prices.items() if p > 0}
            self.account.mark(prices)

            if self._needs_new_bar():
                await self.refresh_analysis()
            if self._analysis_bar is not None and self._analysis_bar != self._last_bar and self.target_weights:
                self._rebalance(prices)
                self._last_bar = self._analysis_bar

            equity = self.account.equity()
            self.storage.store_equity(equity, self.account.cash)
            self.last_cycle = datetime.now().isoformat()
            self._update_portfolio_prediction()
            self._save_state()

            if self.risk_manager.check_max_drawdown(equity):
                self.risk_manager.halted_reason = "Maximum drawdown breached - trading halted"
                send_alert(self.risk_manager.halted_reason, "ERROR")
                self.liquidate()
                self.running = False
        except Exception as e:
            log_error(f"Error in portfolio cycle: {e}", "PortfolioCycle")

    def _needs_new_bar(self) -> bool:
        """Only download candle history every few minutes (a new 4h bar is rare)."""
        last = getattr(self, "_bar_checked", None)
        return last is None or (datetime.now() - last).total_seconds() > 120

    def trading_base(self) -> float:
        """Money the strategy is allowed to deploy: min(equity x budget %, optional $ cap)."""
        equity = max(self.account.equity(), 0.0)
        base = equity * config.TRADE_BUDGET_PCT
        if config.TRADE_BUDGET_USD > 0:
            base = min(base, config.TRADE_BUDGET_USD)
        return base

    def free_funds(self) -> float:
        """Equity not tied up in open positions (what can be withdrawn)."""
        return max(self.account.equity() - self.account.exposure(), 0.0)

    def deposit(self, amount: float) -> Dict:
        if not (amount > 0) or amount > 1e9:
            raise ValueError("Amount must be a positive number")
        self.account.cash += amount
        self.account.initial_capital += amount
        self._after_funds_change("deposit", amount)
        return {"equity": self.account.equity()}

    def withdraw(self, amount: float) -> Dict:
        if not (amount > 0):
            raise ValueError("Amount must be a positive number")
        free = self.free_funds()
        if amount > free + 1e-9:
            raise ValueError(f"Only ${free:,.2f} is free to withdraw (the rest backs open positions)")
        if self.account.initial_capital - amount < 100:
            raise ValueError("The account cannot go below $100 of capital")
        self.account.cash -= amount
        self.account.initial_capital -= amount
        self.risk_manager.peak_adjust -= amount
        self._after_funds_change("withdrawal", amount)
        return {"equity": self.account.equity()}

    def _after_funds_change(self, kind: str, amount: float):
        config.INITIAL_CAPITAL = self.account.initial_capital          # P&L and loss limits use net deposits
        self.settings.setdefault("execution", {})["initial_capital"] = self.account.initial_capital
        self.settings.setdefault("flows", {})["peak_adjust"] = self.risk_manager.peak_adjust
        self._persist_settings()
        self.storage.store_equity(self.account.equity(), self.account.cash)
        self._last_bar = None                                          # re-size positions to the new budget
        self._save_state()
        send_alert(f"{kind.capitalize()} of ${amount:,.2f} (equity ${self.account.equity():,.2f})", "INFO")

    def _rebalance(self, prices: Dict[str, float]):
        equity = self.trading_base()
        allow_new = not (self.risk_manager.check_daily_loss_limit(0)
                         or self.risk_manager.check_weekly_loss_limit(0)
                         or self.risk_manager.check_monthly_loss_limit(0))
        if not allow_new:
            send_alert("Loss limit reached: only reducing positions", "WARNING")

        def signed_value(sym):
            pos = self.account.positions.get(sym)
            if not pos:
                return 0.0
            return pos["size"] * prices.get(sym, pos["mark_price"]) * (1 if pos["side"] == "long" else -1)

        def overweight(item):          # reduce / exit first so gross exposure never overshoots
            sym, w = item
            return abs(signed_value(sym)) - abs(target_value(sym, w))

        # fixed $ per position: every wanted coin gets the same amount (scaled down if it exceeds the budget)
        fixed = config.TRADE_SIZE_USD
        active = [s for s, w in self.target_weights.items() if w != 0]
        per_trade = min(fixed, equity / len(active)) if fixed > 0 and active else 0.0
        ref = per_trade if per_trade > 0 else equity           # scale for the rebalance threshold

        def target_value(sym, w):
            if per_trade > 0:
                return per_trade * (1 if w > 0 else -1) if w != 0 else 0.0
            return w * equity

        trades = 0
        for sym, w in sorted(self.target_weights.items(), key=overweight, reverse=True):
            price = prices.get(sym)
            if not price:
                continue
            cur_val = signed_value(sym)
            tgt_val = target_value(sym, w)
            if w == 0 and cur_val != 0:
                target_units = 0.0
            elif abs(tgt_val - cur_val) < config.REBALANCE_THRESHOLD * ref:
                continue
            else:
                target_units = tgt_val / price
            increases_risk = abs(tgt_val) > abs(cur_val) or (tgt_val * cur_val < 0)
            if increases_risk and not allow_new:
                continue
            for fill in self.account.set_signed_size(sym, target_units, price):
                trades += 1
                rule = f"Target {w:+.0%}"
                kind = "close" if fill["action"] in ("close", "reduce") else "open"
                self._record_fill(fill, kind, {"rule": rule})
                direction = "long" if fill["side"] == "buy" else "short"
                self._add_signal(sym, direction, fill["price"], rule)
                if fill.get("closed"):
                    self.risk_manager.record_pnl(fill["trade_pnl"])
                    self.pair_trades.append({"pnl": fill["trade_pnl"], "reason": "trend_exit",
                                             "strategy": self.strategy_id, "symbol": sym,
                                             "side": fill.get("position_side", "long"),
                                             "time": datetime.now().isoformat()})
                    self.pair_trades = self.pair_trades[-500:]
        if trades:
            send_alert(f"Rebalanced {trades} orders (target exposure "
                       f"{sum(abs(v) for v in self.target_weights.values()):.0%})", "INFO")

    def _update_portfolio_prediction(self):
        exposure = sum(abs(v) for v in self.target_weights.values())
        net = sum(self.target_weights.values())
        if exposure >= 0.5 and net < -0.1:
            self.current_prediction = {"action": "RISK ON · SHORT", "confidence": min(exposure, 1.0), "sentiment": "BEARISH"}
        elif exposure >= 0.5:
            self.current_prediction = {"action": "RISK ON", "confidence": min(exposure, 1.0), "sentiment": "BULLISH"}
        elif exposure > 0.05:
            self.current_prediction = {"action": "PARTIAL", "confidence": 0.5 + exposure / 2, "sentiment": "NEUTRAL"}
        else:
            self.current_prediction = {"action": "RISK OFF", "confidence": 0.6, "sentiment": "NEUTRAL"}

    async def _trading_cycle(self):
        if self.portfolio_mode:
            return await self._portfolio_cycle()
        s1, s2 = self.strategy.pair
        try:
            d1, d2 = await asyncio.gather(
                asyncio.to_thread(self.data_fetcher.fetch_ohlcv, s1, "1m", BARS),
                asyncio.to_thread(self.data_fetcher.fetch_ohlcv, s2, "1m", BARS))
            if d1.empty or d2.empty:
                logger.warning("Market data unavailable; skipping cycle")
                return
            df = pd.merge(d1[['timestamp', 'close']], d2[['timestamp', 'close']],
                          on='timestamp', suffixes=('_1', '_2')).dropna()
            if len(df) < 20:
                logger.warning("Not enough aligned bars; skipping cycle")
                return

            p1, p2 = float(df['close_1'].iloc[-1]), float(df['close_2'].iloc[-1])
            self.account.mark({s1: p1, s2: p2})
            stats = self.strategy.analyze(df['close_1'], df['close_2'])
            self.pair_stats = stats
            self._update_prediction(stats)

            if stats.get("ready"):
                await self._manage_pair(stats["z"], p1, p2)

            equity = self.account.equity()
            self.storage.store_equity(equity, self.account.cash)
            self.last_cycle = datetime.now().isoformat()
            self._save_state()

            # circuit breaker: max drawdown -> liquidate and stop
            if self.risk_manager.check_max_drawdown(equity):
                reason = "Maximum drawdown breached - trading halted"
                self.risk_manager.halted_reason = reason
                send_alert(reason, "ERROR")
                self._close_pair({s1: p1, s2: p2}, "max_drawdown", stats.get("z", 0.0))
                self.running = False
        except Exception as e:
            log_error(f"Error in trading cycle: {e}", "TradingCycle")

    async def _manage_pair(self, z: float, p1: float, p2: float):
        s1, s2 = self.strategy.pair
        prices = {s1: p1, s2: p2}
        current = self._spread_position()
        action = self.strategy.decide(z, current, self.pair_stats.get("std"))

        # pair-level risk stop: unrealised loss beyond 2x the per-trade risk budget
        if current is not None:
            budget = 2 * config.RISK_PER_TRADE * self.account.equity()
            if self.account.unrealized_pnl() <= -budget:
                action = "stop"

        if action in ("close", "stop"):
            self._close_pair(prices, "mean_reversion" if action == "close" else "stop_loss", z)
        elif action in ("open_long", "open_short"):
            allowed, reason = self.risk_manager.can_open_new_position(s1, self.account.list_positions())
            if not allowed:
                if reason != self.risk_manager.halted_reason:
                    self.risk_manager.halted_reason = reason
                    send_alert(f"Entry blocked: {reason}", "WARNING")
                return
            self.risk_manager.halted_reason = None
            self._open_pair(action == "open_long", prices, z)

    def _open_pair(self, long_spread: bool, prices: Dict[str, float], z: float):
        s1, s2 = self.strategy.pair
        notional = self.risk_manager.pair_notional(self.trading_base())
        if config.TRADE_SIZE_USD > 0:
            notional = min(config.TRADE_SIZE_USD, self.trading_base())
        sides = ("long", "short") if long_spread else ("short", "long")
        meta = {"z": round(z, 3), "rule": f"Z-Score: {z:+.2f}"}
        fills = []
        for sym, side in zip((s1, s2), sides):
            fill = self.broker.open_position(sym, side, notional / prices[sym], prices[sym], meta=meta)
            if fill:
                fills.append((sym, side, fill))
        if len(fills) < 2:                      # never leave a half-open pair
            for sym, _, _ in fills:
                self.broker.close_position(sym, prices[sym], "pair_incomplete")
            return
        for sym, side, fill in fills:
            self._record_fill(fill, "open", meta)
            self._add_signal(sym, side, fill["price"], meta["rule"])
        direction = "LONG" if long_spread else "SHORT"
        log_signal({"action": direction, "z": z}, self.strategy.name)
        send_alert(f"Opened {direction} spread {s1}/{s2} (z={z:+.2f}, ${notional:,.0f}/leg)", "INFO")

    def _close_pair(self, prices: Dict[str, float], reason: str, z: float = 0.0):
        if not self.account.positions:
            return
        total = 0.0
        entry_side = self._spread_position()
        for sym in list(self.account.positions):
            fill = self.broker.close_position(sym, prices.get(sym) or self.broker.last_price(sym), reason)
            if fill:
                total += fill["pnl"]
                self._record_fill(fill, "close", {"rule": f"Exit: {reason}"})
        self.risk_manager.record_pnl(total)
        self.pair_trades.append({"pnl": total, "reason": reason, "side": entry_side, "strategy": "pairs",
                                 "time": datetime.now().isoformat()})
        self.pair_trades = self.pair_trades[-500:]
        level = "INFO" if total >= 0 else "WARNING"
        send_alert(f"Closed pair ({reason}). PnL: ${total:+,.2f}", level)

    def _record_fill(self, fill: Dict, kind: str, info: Dict):
        notional = fill["price"] * fill["amount"]
        self.storage.store_trade({
            "order_id": f"paper_{int(datetime.now().timestamp() * 1000)}_{fill['symbol']}",
            "symbol": fill["symbol"], "side": fill["side"], "type": kind,
            "amount": fill["amount"], "price": fill["price"], "fee": fill["fee"],
            "cost": notional, "pnl": fill["pnl"], "status": "closed",
            "timestamp": fill["timestamp"], "info": info,
        })
        self.order_manager.record(fill)

    def _add_signal(self, symbol: str, direction: str, price: float, rule: str):
        now = datetime.now()
        self.recent_signals.insert(0, {
            "symbol": symbol, "direction": direction, "time": now.strftime("%H:%M:%S"),
            "timestamp": int(now.timestamp()), "price": price, "rule": rule})
        self.recent_signals = self.recent_signals[:10]

    def _update_prediction(self, stats: Dict):
        """Translate the spread z-score into a BTC-leg directional bias."""
        if not stats.get("ready"):
            return
        z = stats["z"]
        conf = min(abs(z) / max(config.ENTRY_THRESHOLD, 0.1), 1.0)
        if z <= -1.0:
            self.current_prediction = {"action": "ACCUMULATING", "confidence": conf, "sentiment": "BULLISH"}
        elif z >= 1.0:
            self.current_prediction = {"action": "DISTRIBUTING", "confidence": conf, "sentiment": "BEARISH"}
        else:
            self.current_prediction = {"action": "NEUTRAL", "confidence": 0.5, "sentiment": "NEUTRAL"}

    # --------------------------------------------------------------- liquidate
    def liquidate(self) -> Dict:
        """Close every open paper position immediately at the latest price."""
        positions = self.account.list_positions()
        if not positions:
            return {"closed": 0, "pnl": 0.0}
        total = 0.0
        entry_side = self._spread_position()
        for pos in positions:
            fill = self.broker.close_position(
                pos["symbol"], self.broker.last_price(pos["symbol"]) or pos["mark_price"], "liquidate")
            if fill:
                total += fill["pnl"]
                self._record_fill(fill, "close", {"rule": "Exit: liquidate"})
        self.risk_manager.record_pnl(total)
        self.pair_trades.append({"pnl": total, "reason": "liquidate", "side": entry_side, "strategy": self.strategy_id,
                                 "time": datetime.now().isoformat()})
        self.storage.store_equity(self.account.equity(), self.account.cash)
        self._save_state()
        send_alert(f"Liquidated {len(positions)} positions. PnL: ${total:+,.2f}", "WARNING")
        return {"closed": len(positions), "pnl": total}

    # ------------------------------------------------------------------ status
    def _daily_stats(self) -> Dict:
        today = datetime.now().date().isoformat()
        todays = [t for t in self.pair_trades if t["time"][:10] == today]
        wins = sum(1 for t in self.pair_trades if t["pnl"] > 0)
        n = len(self.pair_trades)
        return {
            "trades": len(todays),
            "pnl": sum(t["pnl"] for t in todays),
            "win_rate": (wins / n) if n else None,      # None = no closed trades yet
            "wins": wins,
            "losses": n - wins,
            "total_trades": n,
            "realized_pnl": sum(t["pnl"] for t in self.pair_trades),
        }

    def recent_events(self, limit: int = 12) -> List[Dict]:
        out = []
        for a in reversed(self.monitor.get_recent_alerts(limit)):
            out.append({"id": a.get("id", 0), "time": a["timestamp"], "level": a["level"], "text": a["message"]})
        return out

    def get_status(self) -> Dict:
        return {
            'running': self.running,
            'mode': 'paper',
            'data_source': self.data_fetcher.data_source,
            'timestamp': datetime.now().isoformat(),
            'last_cycle': self.last_cycle,
            'started_at': self.started_at if self.running else None,
            'risk_metrics': self.risk_manager.get_risk_metrics(),
            'daily_stats': self._daily_stats(),
            'recent_signals': self.recent_signals,
            'prediction': self.current_prediction,
            'strategy': self.portfolio_strategy.name if self.portfolio_mode else self.strategy.name,
            'strategy_id': self.strategy_id,
            'summary': self.describe(),
            'scan': self.scan,
            'analysis_at': self.analysis_at,
            'next_bar_seconds': self.next_bar_seconds() if self.portfolio_mode else None,
            'events': self.recent_events(12),
            'alerts_last_id': self.monitor.alerts_sent[-1]['id'] if self.monitor.alerts_sent else 0,
            'portfolio': {"weights": {k: round(v, 4) for k, v in self.target_weights.items() if v},
                          "exposure": round(sum(abs(v) for v in self.target_weights.values()), 4)},
            'pair': ({"ready": False} if self.portfolio_mode else
                     {"symbols": list(self.strategy.pair), **self.pair_stats,
                      "entry": config.ENTRY_THRESHOLD, "exit": config.EXIT_THRESHOLD}),
            'positions': self.account.list_positions(),
            'capital': {"equity": self.account.equity(), "budget": self.trading_base(),
                        "budget_pct": config.TRADE_BUDGET_PCT, "budget_usd": config.TRADE_BUDGET_USD,
                        "trade_size_usd": config.TRADE_SIZE_USD,
                        "free": self.free_funds(), "deployed": self.account.exposure()},
            'account': {"cash": self.account.cash, "equity": self.account.equity(),
                        "fees_paid": self.account.fees_paid,
                        "initial_capital": self.account.initial_capital},
        }


def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down...")
    if 'bot' in globals():
        bot.stop()
    sys.exit(0)


async def main():
    global bot
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    bot = TradingBot()
    try:
        await bot.initialize()
        if len(sys.argv) > 1 and sys.argv[1] == "backtest":
            start = sys.argv[2] if len(sys.argv) > 2 else "2024-01-01"
            end = sys.argv[3] if len(sys.argv) > 3 else "2024-03-01"
            r = await bot.run_backtest_mode(start, end)
            print(f"Return {r['total_return_percent']:.2%} | trades {r['total_trades']} | "
                  f"win rate {r['win_rate']:.0%} | PF {r['profit_factor']:.2f} | "
                  f"Sharpe {r['sharpe_ratio']:.2f} | maxDD {r['max_drawdown']:.2%}")
        else:
            await bot.run_live_mode()
    except Exception as e:
        log_error(f"Fatal error in main: {e}", "Main")
        send_alert(f"Fatal error: {e}", "ERROR")
        raise
    finally:
        logger.info("Trading bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
