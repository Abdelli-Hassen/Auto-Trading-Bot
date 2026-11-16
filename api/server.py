import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

import config
from api.models import BacktestRequest, BotStatusResponse, FundsRequest, ParamsRequest, SettingsRequest, StartRequest
from utils import settings as cfgmod
from main import TradingBot

logger = logging.getLogger("API")

bot_instance = TradingBot()
bot_task: "asyncio.Task | None" = None
PRICE_SYMBOLS = list(config.SYMBOLS)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        text = json.dumps(message, default=str)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(text)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


async def _fetch_prices() -> Dict[str, Dict[str, float]]:
    async def one(sym):
        try:
            t = await run_in_threadpool(bot_instance.data_fetcher.fetch_ticker, sym)
            return sym, {
                "last": t.get("last", 0) or 0,
                "change": t.get("percentage", 0) or 0,
                "high": t.get("high", 0) or 0,
                "low": t.get("low", 0) or 0,
                "volume": t.get("quoteVolume", 0) or 0,
            }
        except Exception:
            return sym, {"last": 0, "change": 0, "high": 0, "low": 0, "volume": 0}

    return dict(await asyncio.gather(*(one(s) for s in PRICE_SYMBOLS)))


async def _build_payload() -> Dict[str, Any]:
    prices = await _fetch_prices()
    bot_instance.account.mark({s: p["last"] for s, p in prices.items() if p["last"]})
    status = await run_in_threadpool(bot_instance.get_status)
    return {"type": "update", "timestamp": datetime.now().isoformat(), "status": status, "prices": prices}


async def _broadcaster():
    """One shared loop pushes status + prices to every connected client."""
    while True:
        try:
            if manager.active_connections:
                await manager.broadcast(await _build_payload())
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
        await asyncio.sleep(2)


async def _analyst():
    """Keep the strategy's market view fresh even while the bot is stopped."""
    while True:
        try:
            if not bot_instance.running:
                await bot_instance.refresh_analysis()
        except Exception as e:
            logger.error(f"Analysis error: {e}")
        await asyncio.sleep(120)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot_instance.initialize()
    task = asyncio.create_task(_broadcaster())
    analyst = asyncio.create_task(_analyst())
    yield
    task.cancel()
    analyst.cancel()
    bot_instance.stop()
    if bot_task and not bot_task.done():
        bot_task.cancel()


app = FastAPI(title="Trading Bot API (paper trading)", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])


# ------------------------------------------------------------------ control
@app.get("/api/health")
def health():
    return {"ok": True, "mode": "paper", "data_source": bot_instance.data_fetcher.data_source}


@app.get("/api/status", response_model=BotStatusResponse)
def get_status():
    return bot_instance.get_status()


@app.post("/api/bot/start")
async def start_bot(req: StartRequest):
    global bot_task
    if bot_instance.running:
        return {"status": "error", "message": "Bot is already running"}
    if req.mode == "live":
        bot_task = asyncio.create_task(bot_instance.run_live_mode())
        return {"status": "success", "message": "Paper trading started"}
    try:
        results = await bot_instance.run_backtest_mode(
            req.start_date or (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            req.end_date or datetime.now().strftime("%Y-%m-%d"))
    except Exception as e:
        return {"status": "error", "message": f"Backtest failed: {e}"}
    return {"status": "success", "message": "Backtest finished", "results": _summarise(results)}


@app.post("/api/bot/stop")
async def stop_bot():
    if not bot_instance.running:
        return {"status": "error", "message": "Bot is not running"}
    bot_instance.stop()
    return {"status": "success", "message": "Stop signal sent"}


@app.post("/api/bot/liquidate")
async def liquidate_bot():
    """Close every open paper position at the latest price."""
    try:
        result = await run_in_threadpool(bot_instance.liquidate)
    except Exception as e:
        logger.error(f"Failed to liquidate: {e}")
        return {"status": "error", "message": f"Liquidation failed: {e}"}
    if result["closed"] == 0:
        return {"status": "success", "message": "No open positions to close."}
    return {"status": "success",
            "message": f"Closed {result['closed']} positions. Realised PnL: ${result['pnl']:+,.2f}"}


@app.post("/api/bot/reset")
async def reset_account():
    """Reset the paper account to the initial capital and wipe history."""
    try:
        await run_in_threadpool(bot_instance.reset)
    except RuntimeError as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "message": f"Paper account reset to ${config.INITIAL_CAPITAL:,.2f}"}


def _summarise(results: Dict) -> Dict:
    curve = results.get("equity_curve", [])
    step = max(len(curve) // 200, 1)
    out = {k: v for k, v in results.items() if k not in ("equity_curve", "trades")}
    out["equity_curve"] = [{"time": t, "value": round(v, 2)} for t, v in curve[::step]]
    out["trades"] = results.get("trades", [])[-100:]
    return out


@app.post("/api/backtest")
async def run_backtest(req: BacktestRequest):
    """Backtest the strategy on historical bars (does not touch the paper account)."""
    try:
        results = await bot_instance.run_backtest_mode(req.start_date, req.end_date, req.timeframe)
        return {"status": "success", "results": _summarise(results)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------------------------- data
@app.get("/api/status/balance")
def get_balance():
    """Paper account balances."""
    return bot_instance.broker.fetch_balance()


@app.get("/api/positions")
def get_positions():
    return bot_instance.account.list_positions()


def _query(sql: str, params: tuple = ()):
    conn = bot_instance.storage.get_connection()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


@app.get("/api/test/analytics")
def get_analytics(timeframe: str = "all"):
    """Performance analytics computed from the paper trading database."""
    days = {"7d": 7, "30d": 30}.get(timeframe)
    tf = f"AND timestamp >= datetime('now', '-{days} days')" if days else ""

    try:
        equity_rows = _query(f"SELECT timestamp, equity FROM equity WHERE 1=1 {tf} ORDER BY timestamp ASC")
        daily_rows = _query(f"""
            SELECT date(timestamp), SUM(pnl), COUNT(*) FROM trades
            WHERE type = 'close' {tf} GROUP BY date(timestamp) ORDER BY date(timestamp)""")
        symbol_rows = _query(f"""
            SELECT symbol, COUNT(*), SUM(CASE WHEN type = 'close' THEN 1 ELSE 0 END), SUM(pnl)
            FROM trades WHERE 1=1 {tf} GROUP BY symbol""")

        risk = bot_instance.risk_manager.get_risk_metrics()
        daily = bot_instance._daily_stats()
        total_pnl = risk["total_pnl"]
        pct = total_pnl / config.INITIAL_CAPITAL * 100 if config.INITIAL_CAPITAL else 0
        dd = risk["max_drawdown_reached"]
        sharpe, pf = risk["sharpe_ratio"], risk["profit_factor"]

        metrics = [
            {"label": "Total Profit", "value": f"${total_pnl:+,.2f}", "change": f"{pct:+.1f}%", "isPositive": total_pnl >= 0},
            {"label": "Win Rate", "value": ("—" if daily["win_rate"] is None else f"{daily['win_rate'] * 100:.1f}%"), "change": f"{daily['total_trades']} closed trades", "isPositive": (daily["win_rate"] or 0) >= 0.5},
            {"label": "Max Drawdown", "value": f"{dd * 100:.2f}%", "change": "—", "isPositive": dd < 0.05},
            {"label": "Daily P&L", "value": f"${daily['pnl']:+,.2f}", "change": "—", "isPositive": daily["pnl"] >= 0},
            {"label": "Sharpe Ratio", "value": f"{sharpe:.2f}", "change": "—", "isPositive": sharpe >= 1.0},
            {"label": "Profit Factor", "value": f"{pf:.2f}x", "change": "—", "isPositive": pf >= 1.0},
        ]

        step = max(len(equity_rows) // 90, 1)
        chart = [{"date": (r[0] or "")[5:16], "value": round(r[1], 2)} for r in equity_rows[::step]]
        if not chart:
            chart = [{"date": datetime.now().strftime("%H:%M"), "value": round(bot_instance.account.equity(), 2)}]
        elif chart[-1]["value"] != round(bot_instance.account.equity(), 2):
            chart.append({"date": datetime.now().strftime("%m-%d %H:%M"),
                          "value": round(bot_instance.account.equity(), 2)})

        daily_chart = [{"date": r[0] or "—", "pnl": round(r[1] or 0.0, 2), "trades": r[2] or 0} for r in daily_rows]
        symbol_perf = [{"symbol": r[0], "total": r[1], "sells": r[2], "pnl": round(r[3] or 0.0, 2)} for r in symbol_rows]
        return {"metrics": metrics, "chartData": chart, "dailyChart": daily_chart, "symbolPerf": symbol_perf}
    except Exception as e:
        logger.error(f"Analytics endpoint error: {e}")
        return {"metrics": [], "chartData": [{"date": "Start", "value": config.INITIAL_CAPITAL}],
                "dailyChart": [], "symbolPerf": []}


@app.get("/api/test/ohlcv")
async def get_ohlcv(symbol: str = "BTC/USDT", timeframe: str = "1m", limit: int = 100):
    """OHLCV candles in lightweight-charts format."""
    limit = max(1, min(limit, 1000))
    try:
        df = await run_in_threadpool(bot_instance.data_fetcher.fetch_ohlcv, symbol, timeframe, limit)
        if df.empty:
            return []
        return [{"time": int(r.timestamp.timestamp()), "open": float(r.open), "high": float(r.high),
                 "low": float(r.low), "close": float(r.close), "volume": float(r.volume)}
                for r in df.itertuples()]
    except Exception as e:
        logger.error(f"Error in get_ohlcv: {e}")
        return []


STRATEGY_META = {
    "trend_momentum": {
        "name": "Trend + Momentum", "type": "Trend Following · Momentum", "risk": "Medium",
        "universe": "BTC ETH SOL BNB XRP ADA DOGE LINK",
        "description": ("Long/flat portfolio of 8 large caps on 4h bars. Half Donchian-breakout trend following, "
                        "half cross-sectional momentum (top 3 coins above their trend, only when BTC is in an "
                        "uptrend), scaled to a volatility target. No leverage, no shorting; moves to cash when "
                        "nothing is trending."),
        "rules": ["Rebalances on each new 4h bar close", "Breakout lookbacks 120/240/480 bars",
                  "Momentum lookbacks 90/180/360 bars, top 3", "BTC must be above its 480-bar EMA"],
    },
    "trend_momentum_ls": {
        "name": "Trend + Momentum Long/Short", "type": "Trend Following · Momentum · Shorts", "risk": "High",
        "universe": "BTC ETH SOL BNB XRP ADA DOGE LINK",
        "description": ("Same engine as Trend + Momentum, but it can also SHORT coins that are breaking down, so it "
                        "keeps working (and earns) in falling markets instead of sitting in cash. Always active, "
                        "higher drawdowns: backtested max drawdown ~40% vs ~28% for the long-only version, and "
                        "slightly lower risk-adjusted return overall. Still checks the market every 4h bar."),
        "rules": ["Shorts coins that break their 20/40/80-day lows", "Shorts the 3 weakest coins only while BTC is in a downtrend",
                  "Gross exposure never above 100%, no leverage", "Rebalances on each new 4h bar close"],
    },
    "pairs": {
        "name": "Pairs Trading", "type": "Statistical Arbitrage", "risk": "Medium",
        "universe": "BTC / ETH",
        "description": ("Dollar-neutral long/short on the BTC/ETH log-price spread. Enters when the spread z-score "
                        "is stretched and the expected reversion beats trading costs; exits when it normalises."),
        "rules": ["1-minute bars, 60-bar rolling hedge ratio", "Skips trades whose edge is below costs",
                  "Pair-level stop at 2x risk budget"],
    },
}


def _strategy_card(sid: str) -> dict:
    meta = STRATEGY_META[sid]
    defs = cfgmod.STRATEGY_PARAMS[sid]
    values = bot_instance.get_params(sid)
    selected = sid == bot_instance.strategy_id
    return {
        "id": sid, **meta,
        "selected": selected,
        "status": "active" if (selected and bot_instance.running) else ("selected" if selected else "inactive"),
        "stats": bot_instance.strategy_stats(sid),
        "params": [{"key": k, "value": values[k], **d} for k, d in defs.items()],
        "backtest": bot_instance.backtests.get(sid),
        "summary": bot_instance.describe() if selected else None,
        "open_positions": len(bot_instance.account.positions) if selected else 0,
    }


@app.get("/api/strategies")
def list_strategies():
    return [_strategy_card(sid) for sid in STRATEGY_META]


@app.post("/api/strategies/{sid}/select")
async def select_strategy(sid: str):
    try:
        bot_instance.select_strategy(sid)
    except (ValueError, RuntimeError) as e:
        return {"status": "error", "message": str(e)}
    asyncio.create_task(bot_instance.refresh_analysis())
    return {"status": "success", "message": f"{STRATEGY_META[sid]['name']} selected"}


@app.post("/api/strategies/{sid}/start")
async def start_strategy(sid: str):
    global bot_task
    if sid not in STRATEGY_META:
        return {"status": "error", "message": "Unknown strategy"}
    if bot_instance.running and sid != bot_instance.strategy_id:
        return {"status": "error", "message": "Another strategy is running. Stop it first."}
    try:
        bot_instance.select_strategy(sid)
    except (ValueError, RuntimeError) as e:
        return {"status": "error", "message": str(e)}
    if bot_instance.running:
        return {"status": "error", "message": "Already running"}
    bot_task = asyncio.create_task(bot_instance.run_live_mode())
    return {"status": "success", "message": f"{STRATEGY_META[sid]['name']} started"}


@app.post("/api/strategies/{sid}/stop")
async def stop_strategy(sid: str):
    if not bot_instance.running or sid != bot_instance.strategy_id:
        return {"status": "error", "message": "This strategy is not running"}
    bot_instance.stop()
    return {"status": "success", "message": "Stop signal sent"}


@app.put("/api/strategies/{sid}/params")
def update_params(sid: str, req: ParamsRequest):
    try:
        values = bot_instance.update_params(sid, req.params)
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "params": values}


@app.post("/api/strategies/{sid}/backtest")
async def strategy_backtest(sid: str):
    if sid not in STRATEGY_META:
        return {"status": "error", "message": "Unknown strategy"}
    try:
        res = await bot_instance.run_strategy_backtest(sid)
    except Exception as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "backtest": res}


@app.get("/api/test/strategies")
def get_strategies():
    """Legacy alias."""
    return list_strategies()


@app.get("/api/settings")
def get_settings():
    return {"values": cfgmod.current_values(), "schema": cfgmod.schema(),
            "data_source": bot_instance.data_fetcher.data_source, "exchange": config.EXCHANGE,
            "running": bot_instance.running}


@app.put("/api/settings")
def put_settings(req: SettingsRequest):
    try:
        values = bot_instance.update_settings(req.risk, req.execution)
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "values": values}


@app.post("/api/account/deposit")
def deposit(req: FundsRequest):
    try:
        res = bot_instance.deposit(req.amount)
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "message": f"Deposited ${req.amount:,.2f}", **res}


@app.post("/api/account/withdraw")
def withdraw(req: FundsRequest):
    try:
        res = bot_instance.withdraw(req.amount)
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    return {"status": "success", "message": f"Withdrew ${req.amount:,.2f}", **res}


@app.get("/api/account")
def get_account():
    st = bot_instance.get_status()
    return {"account": st["account"], "risk": st["risk_metrics"], "daily": st["daily_stats"],
            "positions": st["positions"], "strategy": st["strategy_id"], "data_source": st["data_source"],
            "mode": "paper", "exchange": config.EXCHANGE}


def _format_time(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(str(ts))
        days = (datetime.now() - dt).days
        if days == 0:
            return dt.strftime("%I:%M:%S %p")
        return "Yesterday" if days == 1 else dt.strftime("%b %d")
    except Exception:
        return str(ts)[:16] if ts else "—"


@app.get("/api/test/history")
def get_history():
    """Paper trade fills, newest first."""
    try:
        rows = _query("""SELECT id, timestamp, symbol, side, amount, price, cost, status, fee, type, pnl
                         FROM trades ORDER BY id DESC LIMIT 200""")
    except Exception as e:
        logger.error(f"History endpoint error: {e}")
        return []
    result = []
    for tid, ts, symbol, side, amount, price, cost, status, fee, kind, pnl in rows:
        pnl = pnl or 0.0
        base = symbol.split("/")[0] if symbol else ""
        result.append({
            "id": f"TRD-{tid}", "rawId": tid, "timestamp": str(ts or ""), "time": _format_time(ts),
            "symbol": symbol or "—",
            "type": "Buy" if str(side).lower() == "buy" else "Sell",
            "kind": kind or "",
            "amount": f"{amount:.4f} {base}" if amount else "—", "rawAmount": amount or 0.0,
            "price": f"${price:,.2f}" if price else "—", "rawPrice": price or 0.0,
            "cost": f"${cost:,.2f}" if cost else "—",
            "rawCost": cost or 0.0,
            "rawPnl": pnl,
            "fee": f"${fee:,.4f}" if fee else "—",
            "pnl": f"${pnl:+,.2f}" if (kind == "close" or pnl) else "—",
            "status": status or "closed",
        })
    return result


@app.get("/api/test/notifications")
async def get_notifications():
    raw = bot_instance.monitor.get_recent_alerts(limit=20)
    level_map = {"ERROR": "error", "WARNING": "warning", "INFO": "info", "SUCCESS": "success"}
    now = datetime.now()
    result = []
    for i, alert in enumerate(reversed(raw)):
        try:
            secs = int((now - datetime.fromisoformat(alert["timestamp"])).total_seconds())
            time_str = (f"{secs}s ago" if secs < 60 else f"{secs // 60} mins ago" if secs < 3600
                        else f"{secs // 3600} hours ago" if secs < 86400 else f"{secs // 86400} days ago")
        except Exception:
            time_str = "—"
        msg = alert.get("message", "")
        result.append({"id": alert.get("id", i + 1), "type": level_map.get(alert.get("level", "INFO").upper(), "info"),
                       "title": (msg.split(":")[0] if ":" in msg else msg)[:30], "message": msg, "time": time_str})
    return result


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # send a full snapshot immediately so the UI never shows empty placeholders
        await websocket.send_text(json.dumps(await _build_payload(), default=str))
        while True:
            await websocket.receive_text()   # keeps the connection alive; client sends nothing
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
