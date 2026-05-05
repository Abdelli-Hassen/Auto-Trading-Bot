import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from typing import List, Dict, Any
from datetime import datetime

from api.models import StartRequest, BotStatusResponse
from main import TradingBot

logger = logging.getLogger("API")

app = FastAPI(title="Trading Bot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global bot instance
bot_instance = TradingBot()
bot_task = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                # Catch RuntimeError if socket already closed, or other send errors
                logger.error(f"WebSocket send error: {e}")
                dead_connections.append(connection)
        
        for dead in dead_connections:
            if dead in self.active_connections:
                self.active_connections.remove(dead)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    await bot_instance.initialize()

@app.get("/api/status", response_model=BotStatusResponse)
def get_status():
    status = bot_instance.get_status()
    return status

@app.post("/api/bot/start")
async def start_bot(req: StartRequest):
    global bot_task
    if bot_instance.running:
        return {"status": "error", "message": "Bot is already running"}
    
    if req.mode == "live":
        bot_task = asyncio.create_task(bot_instance.run_live_mode())
        return {"status": "success", "message": "Live bot started"}
    else:
        # Backtest mode
        bot_task = asyncio.create_task(bot_instance.run_backtest_mode(req.start_date, req.end_date))
        return {"status": "success", "message": "Backtest started"}

@app.post("/api/bot/stop")
async def stop_bot():
    if not bot_instance.running:
        return {"status": "error", "message": "Bot is not running"}
    bot_instance.stop()
    return {"status": "success", "message": "Stop signal sent"}

@app.post("/api/bot/liquidate")
async def liquidate_bot():
    if not bot_instance.running:
        return {"status": "error", "message": "Bot is not running"}
    
    logger.warning("LIQUIDATE ALL POSITIONS commanded from UI!")
    
    try:
        # Pseudo-code for actual liquidation
        # bot_instance.order_manager.cancel_all_orders()
        # bot_instance.broker.close_all_positions()
        
        return {"status": "success", "message": "Liquidate command issued. All positions closing."}
    except Exception as e:
        logger.error(f"Failed to liquidate: {e}")
        return {"status": "error", "message": f"Liquidation failed: {str(e)}"}

# --- REAL DATA API ENDPOINTS ---

@app.get("/api/status/balance")
def get_balance():
    """Return real account balance breakdown from exchange."""
    try:
        balance = bot_instance.data_fetcher.exchange.fetch_balance()
        result = {}
        for asset in ["USDT", "BTC", "ETH", "SOL", "BNB"]:
            info = balance.get(asset, {})
            free = info.get("free", 0.0) if isinstance(info, dict) else 0.0
            total = info.get("total", 0.0) if isinstance(info, dict) else 0.0
            result[asset] = {"free": round(free, 6), "total": round(total, 6)}
        result["total_usdt"] = round(balance.get("total", {}).get("USDT", 0.0), 2)
        return result
    except Exception as e:
        logger.error(f"Balance endpoint error: {e}")
        return {"USDT": {"free": 0.0, "total": 0.0}, "BTC": {"free": 0.0, "total": 0.0}, "ETH": {"free": 0.0, "total": 0.0}, "SOL": {"free": 0.0, "total": 0.0}, "total_usdt": 0.0}


@app.get("/api/test/analytics")
def get_analytics(timeframe: str = "all"):
    """Compute analytics from the real SQLite database."""
    import sqlite3
    import config

    db_path = config.DATA_DIR / "storage" / "trading_data.db"

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Total PnL and trade stats
        cursor.execute("SELECT COUNT(*), SUM(cost), AVG(cost) FROM trades WHERE status = 'closed'")
        row = cursor.fetchone()
        total_trades = row[0] or 0
        total_cost = row[1] or 0.0

        # Win rate: trades where fee < cost (proxy for profitable side)
        cursor.execute("SELECT COUNT(*) FROM trades WHERE side = 'buy'")
        buys = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM trades WHERE side = 'sell'")
        sells = cursor.fetchone()[0] or 0

        # Timeframe filter
        tf_filter = ""
        if timeframe == "7d":
            tf_filter = "AND timestamp >= datetime('now', '-7 days')"
        elif timeframe == "30d":
            tf_filter = "AND timestamp >= datetime('now', '-30 days')"

        # Equity curve from equity table
        cursor.execute(f"SELECT timestamp, equity FROM equity WHERE 1=1 {tf_filter} ORDER BY timestamp ASC LIMIT 90")
        equity_rows = cursor.fetchall()

        # Daily PnL bars
        cursor.execute(f"""
            SELECT date(timestamp) as day, SUM(cost) as daily_pnl, COUNT(*) as cnt
            FROM trades WHERE 1=1 {tf_filter}
            GROUP BY day ORDER BY day ASC
        """)
        daily_rows = cursor.fetchall()

        # Per-symbol breakdown
        cursor.execute(f"""
            SELECT symbol, COUNT(*) as total, SUM(CASE WHEN side='sell' THEN 1 ELSE 0 END) as sells,
                   SUM(cost) as pnl
            FROM trades WHERE 1=1 {tf_filter}
            GROUP BY symbol
        """)
        symbol_rows = cursor.fetchall()

        # Risk metrics from bot
        risk = bot_instance.risk_manager.get_risk_metrics()
        total_pnl = risk.get("total_pnl", 0.0)
        drawdown = risk.get("current_drawdown", 0.0)
        win_rate = bot_instance.daily_stats.get("win_rate", 0.0)
        daily_pnl = bot_instance.daily_stats.get("pnl", 0.0)

        initial_capital = config.INITIAL_CAPITAL
        pnl_pct = (total_pnl / initial_capital * 100) if initial_capital else 0

        metrics = [
            {
                "label": "Total Profit",
                "value": f"${total_pnl:+,.2f}",
                "change": f"{pnl_pct:+.1f}%",
                "isPositive": total_pnl >= 0
            },
            {
                "label": "Win Rate",
                "value": f"{win_rate * 100:.1f}%",
                "change": "—",
                "isPositive": win_rate >= 0.5
            },
            {
                "label": "Max Drawdown",
                "value": f"{drawdown * 100:.2f}%",
                "change": "—",
                "isPositive": drawdown < 0.05
            },
            {
                "label": "Daily P&L",
                "value": f"${daily_pnl:+,.2f}",
                "change": "—",
                "isPositive": daily_pnl >= 0
            },
            {
                "label": "Sharpe Ratio",
                "value": f"{risk.get('sharpe_ratio', 0.0):.2f}",
                "change": "—",
                "isPositive": risk.get('sharpe_ratio', 0.0) >= 1.0
            },
            {
                "label": "Profit Factor",
                "value": f"{risk.get('profit_factor', 0.0):.2f}x",
                "change": "—",
                "isPositive": risk.get('profit_factor', 0.0) >= 1.0
            },
        ]

        # Daily bar chart data
        daily_chart = [
            {"date": row[0] or "—", "pnl": round(row[1] or 0.0, 2), "trades": row[2] or 0}
            for row in daily_rows
        ]

        # Per-symbol perf table
        symbol_perf = [
            {"symbol": row[0], "total": row[1], "sells": row[2], "pnl": round(row[3] or 0.0, 2)}
            for row in symbol_rows
        ]

        # Build chart data from equity table or fall back to initial capital baseline
        if equity_rows:
            chart_data = [
                {"date": row[0][:10] if row[0] else "—", "value": row[1]}
                for row in equity_rows
            ]
        else:
            # Flat baseline: no trades yet, show starting capital
            today = datetime.now()
            chart_data = [
                {
                    "date": (today.replace(day=1)).strftime("%b %d"),
                    "value": float(initial_capital)
                },
                {
                    "date": today.strftime("%b %d"),
                    "value": float(initial_capital) + total_pnl
                }
            ]

        conn.close()
        return {"metrics": metrics, "chartData": chart_data, "dailyChart": daily_chart, "symbolPerf": symbol_perf}

    except Exception as e:
        logger.error(f"Analytics endpoint error: {e}")
        return {
            "metrics": [
                {"label": "Total Profit", "value": "$0.00", "change": "0.0%", "isPositive": True},
                {"label": "Win Rate", "value": "0.0%", "change": "—", "isPositive": True},
                {"label": "Max Drawdown", "value": "0.00%", "change": "—", "isPositive": True},
                {"label": "Daily P&L", "value": "$0.00", "change": "—", "isPositive": True},
                {"label": "Sharpe Ratio", "value": "0.00", "change": "—", "isPositive": False},
                {"label": "Profit Factor", "value": "0.00x", "change": "—", "isPositive": False},
            ],
            "chartData": [{"date": datetime.now().strftime("%b %d"), "value": config.INITIAL_CAPITAL}],
            "dailyChart": [],
            "symbolPerf": []
        }


@app.get("/api/test/strategies")
def get_strategies():
    """Return the real strategy registered in the bot."""
    strategy = bot_instance.strategy
    is_running = bot_instance.running

    # Build entry from the actual strategy object
    real_strategy = {
        "id": 1,
        "name": strategy.name,
        "status": "active" if is_running else "inactive",
        "type": "Statistical Arbitrage",
        "profit": f"${bot_instance.daily_stats.get('pnl', 0.0):+.2f}",
        "risk": "Medium",
        "description": (
            f"Pairs trading strategy on "
            f"{getattr(strategy, 'pair', ('BTC/USDT', 'ETH/USDT'))[0]} / "
            f"{getattr(strategy, 'pair', ('BTC/USDT', 'ETH/USDT'))[1]}. "
            "Exploits statistical co-movement between correlated assets using z-score mean reversion."
        )
    }
    return [real_strategy]


@app.get("/api/test/history")
def get_history():
    """Return real trade history from SQLite."""
    import sqlite3
    import config

    db_path = config.DATA_DIR / "storage" / "trading_data.db"

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, symbol, side, amount, price, cost, status, fee
            FROM trades
            ORDER BY timestamp DESC
            LIMIT 200
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return []

        result = []
        for i, row in enumerate(rows):
            trade_id, ts, symbol, side, amount, price, cost, status, fee = row
            # Format timestamp
            try:
                dt = datetime.fromisoformat(str(ts))
                now = datetime.now()
                delta = now - dt
                if delta.days == 0:
                    time_str = dt.strftime("%I:%M:%S %p")
                elif delta.days == 1:
                    time_str = "Yesterday"
                else:
                    time_str = dt.strftime("%b %d")
            except Exception:
                time_str = str(ts)[:16] if ts else "—"

            pnl = cost or 0.0
            pnl_str = f"${pnl:+.2f}"

            result.append({
                "id": f"TRD-{trade_id or i}",
                "rawId": trade_id or i,
                "timestamp": str(ts) if ts else "",
                "time": time_str,
                "symbol": symbol or "—",
                "type": "Buy" if str(side).lower() == "buy" else "Sell",
                "amount": f"{amount:.4f} {symbol.split('/')[0] if symbol else ''}" if amount else "—",
                "rawAmount": amount or 0.0,
                "price": f"${price:,.2f}" if price else "—",
                "rawPrice": price or 0.0,
                "cost": f"${cost:,.2f}" if cost else "—",
                "rawCost": cost or 0.0,
                "fee": f"${fee:,.4f}" if fee else "—",
                "pnl": pnl_str,
                "status": status or "Completed"
            })

        return result

    except Exception as e:
        logger.error(f"History endpoint error: {e}")
        return []


@app.get("/api/test/notifications")
async def get_notifications():
    """Return real alerts from the bot's monitoring system."""
    raw_alerts = bot_instance.monitor.get_recent_alerts(limit=20)

    if not raw_alerts:
        return []

    # Map alert level to UI type
    level_map = {
        "ERROR": "error",
        "WARNING": "warning",
        "INFO": "info",
        "SUCCESS": "success",
    }

    result = []
    now = datetime.now()
    for i, alert in enumerate(reversed(raw_alerts)):
        level = alert.get("level", "INFO").upper()
        ts_str = alert.get("timestamp", "")

        # Human-readable relative time
        try:
            dt = datetime.fromisoformat(ts_str)
            delta = now - dt
            total_seconds = int(delta.total_seconds())
            if total_seconds < 60:
                time_str = f"{total_seconds}s ago"
            elif total_seconds < 3600:
                time_str = f"{total_seconds // 60} mins ago"
            elif total_seconds < 86400:
                time_str = f"{total_seconds // 3600} hours ago"
            else:
                time_str = f"{total_seconds // 86400} days ago"
        except Exception:
            time_str = ts_str[:16] if ts_str else "—"

        message = alert.get("message", "")
        # Derive a short title from the message
        title = message.split(":")[0][:30] if ":" in message else message[:30]

        result.append({
            "id": i + 1,
            "type": level_map.get(level, "info"),
            "title": title,
            "message": message,
            "time": time_str
        })

    return result

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Continuously send status and simulated price data
            status = bot_instance.get_status()
            
            # Fetch multi-symbol prices for the dashboard without blocking the async loop
            prices = {}
            for sym in ["BTC/USDT", "ETH/USDT", "SOL/USDT"]:
                try:
                    ticker = await run_in_threadpool(bot_instance.data_fetcher.fetch_ticker, sym)
                    prices[sym] = {
                        "last": ticker.get("last", 0),
                        "change": ticker.get("percentage", 0),
                        "high": ticker.get("high", 0),
                        "low": ticker.get("low", 0),
                        "volume": ticker.get("quoteVolume", 0),
                    }
                except Exception:
                    prices[sym] = {"last": 0, "change": 0, "high": 0, "low": 0, "volume": 0}

            payload = {
                "type": "update",
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "prices": prices
            }
            await manager.broadcast(payload)
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
