from __future__ import annotations

import json
import logging
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request
from flask_cors import CORS
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView

import config
from data.fetcher import DataFetcher
from data.storage import DataStorage
from execution.broker import Broker
from monitoring import get_monitor, send_alert
from risk.manager import RiskManager


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DesignPythonDesktop")

PROJECT_ROOT = Path(__file__).parent
DESIGN_ROOT = PROJECT_ROOT / "design python"

PAGES = {
    "dashboard": DESIGN_ROOT / "executive_dashboard" / "code.html",
    "positions": DESIGN_ROOT / "positions_order_book" / "code.html",
    "analytics": DESIGN_ROOT / "strategy_analytics" / "code.html",
    "configuration": DESIGN_ROOT / "configuration_settings" / "code.html",
    "logs": DESIGN_ROOT / "system_logs_monitoring" / "code.html",
}

NAV_MAP = {
    "dashboard": "/dashboard",
    "analytics": "/analytics",
    "positions": "/positions",
    "logs": "/logs",
    "settings": "/configuration",
}

app = Flask(__name__)
CORS(app)
logging.getLogger("werkzeug").setLevel(logging.WARNING)


class BotRuntime:
    def __init__(self):
        self.testnet = config.TESTNET
        self.storage = DataStorage()
        self.fetcher = DataFetcher(testnet=self.testnet)
        self.broker = Broker(testnet=self.testnet)
        self.risk = RiskManager(self.storage)
        self.monitor = get_monitor()
        self.trading_bot = None
        self.bot_thread = None
        self.bot_running = False

    def start_trading_bot(self):
        """Start the trading bot in a separate thread."""
        if self.bot_running:
            return {"ok": False, "message": "Bot is already running"}
        
        try:
            # Import here to avoid circular imports
            from main import TradingBot
            import asyncio
            
            def run_bot():
                # Create new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Create and run the bot
                bot = TradingBot()
                loop.run_until_complete(bot.initialize())
                loop.run_until_complete(bot.run_live_mode())
            
            self.bot_thread = threading.Thread(target=run_bot, daemon=True)
            self.bot_thread.start()
            self.bot_running = True
            
            send_alert("Trading bot started from UI", "INFO")
            return {"ok": True, "message": "Trading bot started"}
        except Exception as e:
            logger.error(f"Failed to start trading bot: {e}")
            send_alert(f"Failed to start trading bot: {e}", "ERROR")
            return {"ok": False, "message": f"Failed to start bot: {str(e)}"}

    def stop_trading_bot(self):
        """Stop the trading bot."""
        if not self.bot_running:
            return {"ok": False, "message": "Bot is not running"}
        
        try:
            # Note: This is a simplified stop - in practice you'd need to signal the bot to stop
            # For now, we'll just mark it as not running (the bot checks its own running flag)
            self.bot_running = False
            send_alert("Trading bot stop requested from UI", "WARNING")
            return {"ok": True, "message": "Trading bot stop requested"}
        except Exception as e:
            logger.error(f"Failed to stop trading bot: {e}")
            return {"ok": False, "message": f"Failed to stop bot: {str(e)}"}

    def get_bot_status(self):
        """Get current bot status."""
        return {
            "running": self.bot_running,
            "mode": "TESTNET" if self.testnet else "LIVE"
        }
        self.trading_bot = None
        self.bot_thread = None
        self.bot_running = False

    def reload_clients(self):
        self.fetcher = DataFetcher(testnet=self.testnet)
        self.broker = Broker(testnet=self.testnet)

    def get_state(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "mode": "TESTNET_MODE" if self.testnet else "LIVE_MODE",
            "system_status": "SYSTEM_RUNNING",
            "exchange": config.EXCHANGE,
            "symbols": config.SYMBOLS,
            "has_api_keys": bool(config.API_KEY and config.API_SECRET),
            "api_key_masked": (f"{config.API_KEY[:6]}...{config.API_KEY[-4:]}" if config.API_KEY else ""),
        }

        try:
            bal = self.broker.fetch_balance()
            state["balance_usdt"] = (
                bal.get("total", {}).get("USDT") if isinstance(bal, dict) else None
            )
            if isinstance(bal, dict):
                totals = bal.get("total", {}) or {}
                holdings = [
                    {"asset": asset, "amount": amount}
                    for asset, amount in totals.items()
                    if isinstance(amount, (int, float)) and amount and amount > 0
                ]
                holdings = sorted(holdings, key=lambda x: x["amount"], reverse=True)[:12]
                state["holdings"] = holdings
            else:
                state["holdings"] = []
        except Exception as exc:
            logger.warning("Balance fetch failed: %s", exc)
            state["balance_usdt"] = None
            state["holdings"] = []

        try:
            state["positions"] = self.broker.fetch_positions() or []
        except Exception as exc:
            logger.warning("Positions fetch failed: %s", exc)
            state["positions"] = []

        try:
            ticker_btc = self.fetcher.fetch_ticker("BTC/USDT")
            ticker_eth = self.fetcher.fetch_ticker("ETH/USDT")
            state["btc_last"] = ticker_btc.get("last") if isinstance(ticker_btc, dict) else None
            state["eth_last"] = ticker_eth.get("last") if isinstance(ticker_eth, dict) else None
        except Exception as exc:
            logger.warning("Ticker fetch failed: %s", exc)
            state["btc_last"] = None
            state["eth_last"] = None

        try:
            orderbook = self.fetcher.fetch_order_book("BTC/USDT", limit=10)
            state["orderbook_btc"] = {
                "bids": orderbook.get("bids", [])[:10],
                "asks": orderbook.get("asks", [])[:10],
            }
        except Exception:
            state["orderbook_btc"] = {"bids": [], "asks": []}

        try:
            trades = self.fetcher.fetch_trades("BTC/USDT", limit=15)
            state["recent_trades"] = trades[:15]
        except Exception:
            state["recent_trades"] = []

        try:
            state["risk"] = self.risk.get_risk_metrics()
        except Exception as exc:
            logger.warning("Risk fetch failed: %s", exc)
            state["risk"] = {}

        try:
            stats = self.storage.get_stats()
            state["trade_count"] = stats.get("trade_count", 0)
        except Exception:
            state["trade_count"] = 0

        state["alerts"] = self.monitor.get_recent_alerts(20)
        return state

    def handle_ui_action(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = str(payload.get("action", "")).strip()
        page = str(payload.get("page", "")).strip()
        symbol = str(payload.get("symbol", "")).strip()
        value = payload.get("value")
        logger.info("UI action: page=%s action=%s payload=%s", page, action, payload)

        low = action.lower()
        result = {"ok": True, "message": f"Action captured: {action}"}

        if "save parameters" in low:
            send_alert("Configuration Save requested from UI", "INFO")
            result["message"] = "Parameters save request accepted"
        elif "discard changes" in low:
            result["message"] = "Changes discarded (UI state only)"
        elif "terminate" in low:
            send_alert("Bot terminate requested from UI", "WARNING")
            result["message"] = "Terminate requested"
        elif "initialize" in low:
            send_alert("Bot initialize requested from UI", "INFO")
            result["message"] = "Initialize requested"
        elif "buy spread" in low:
            send_alert("Manual BUY spread requested", "INFO")
            result["message"] = "Buy spread request sent"
        elif "sell spread" in low:
            send_alert("Manual SELL spread requested", "INFO")
            result["message"] = "Sell spread request sent"
        elif "force liquidate" in low:
            send_alert("Force liquidate requested", "WARNING")
            result["message"] = "Force liquidation requested"
        elif "close" in low:
            if symbol:
                send_alert(f"Close requested for {symbol}", "INFO")
                result["message"] = f"Close requested for {symbol}"
            else:
                send_alert("Close position requested", "INFO")
                result["message"] = "Close position requested"
        elif page == "configuration" and action == "":
            # Handles unlabeled toggle inputs from the exact design template.
            if isinstance(value, bool):
                self.testnet = bool(value)
                self.reload_clients()
                send_alert(f"Runtime mode switched to {'TESTNET' if self.testnet else 'LIVE'}", "INFO")
                result["message"] = f"Mode switched to {'TESTNET' if self.testnet else 'LIVE'} (runtime)"
            else:
                result["message"] = "Configuration value captured"
        
        # Auto trading mode controls
        elif "start auto mode" in low or "enable auto trading" in low:
            result = self.start_trading_bot()
        elif "stop auto mode" in low or "disable auto trading" in low or "stop bot" in low:
            result = self.stop_trading_bot()
            
        return result


runtime = BotRuntime()

INJECT_JS = r"""
<script>
(function(){
  const PAGE = window.location.pathname.replace("/", "") || "dashboard";

  function mapNavLinks() {
    const map = { dashboard:"/dashboard", analytics:"/analytics", positions:"/positions", logs:"/logs", settings:"/configuration" };
    document.querySelectorAll("a").forEach(a => {
      const t = (a.textContent || "").toLowerCase();
      if (t.includes("dashboard")) a.setAttribute("href", map.dashboard);
      else if (t.includes("analytics")) a.setAttribute("href", map.analytics);
      else if (t.includes("positions")) a.setAttribute("href", map.positions);
      else if (t.includes("logs")) a.setAttribute("href", map.logs);
      else if (t.includes("settings")) a.setAttribute("href", map.settings);
    });
  }

  async function postAction(action, extra) {
    try {
      const payload = Object.assign({ page: PAGE, action: action }, extra || {});
      const res = await fetch("/api/ui-action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      showToast(data.message || "Action executed");
    } catch (e) {
      showToast("Action failed: " + e.message, true);
    }
  }

  function bindInteractiveElements() {
    document.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", function(ev){
        const txt = (btn.textContent || "").trim().replace(/\s+/g, " ");
        postAction(txt || "button_click", { symbol: btn.dataset.symbol || "" });
      });
    });
    document.querySelectorAll("input, select, textarea").forEach(el => {
      el.addEventListener("change", function(){
        const label = (el.closest("div")?.querySelector("label")?.textContent || el.name || el.id || "input_change").trim();
        const val = (el.type === "checkbox") ? !!el.checked : el.value;
        postAction(label, { value: val });
      });
    });
  }

  function ensureToast() {
    if (document.getElementById("__py_toast")) return;
    const toast = document.createElement("div");
    toast.id = "__py_toast";
    toast.style.cssText = "position:fixed;right:16px;bottom:16px;z-index:99999;background:#171f33;border:1px solid #3e484f;color:#dae2fd;padding:10px 12px;border-radius:4px;font-family:Inter,sans-serif;font-size:12px;opacity:0;transition:opacity .2s;";
    document.body.appendChild(toast);
  }

  function showToast(msg, error) {
    ensureToast();
    const t = document.getElementById("__py_toast");
    t.textContent = msg;
    t.style.borderColor = error ? "#ff6b6b" : "#38bdf8";
    t.style.opacity = "1";
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => t.style.opacity = "0", 1800);
  }
  window.showToast = showToast;

  function setSystemLabel(mode, status) {
    document.querySelectorAll("*").forEach(el => {
      if (!el.childElementCount) {
        const tx = (el.textContent || "").trim();
        if (tx === "SYSTEM_RUNNING") el.textContent = status || "SYSTEM_RUNNING";
        if (tx === "TESTNET_MODE" || tx === "LIVE_MODE") el.textContent = mode || tx;
      }
    });
  }

  function updateDashboard(state) {
    const metrics = document.querySelectorAll("div.font-data-lg.text-data-lg");
    if (metrics.length >= 4) {
      const equity = state.balance_usdt != null ? `$${Number(state.balance_usdt).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}` : "N/A";
      const pnl = Number(state.risk?.daily_pnl || 0);
      const trades = Number(state.trade_count || 0);
      const wr = "N/A";
      metrics[0].textContent = equity;
      metrics[1].textContent = `${pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}`;
      metrics[2].textContent = String(trades);
      metrics[3].textContent = wr;
      metrics[1].style.color = pnl >= 0 ? "#4edea3" : "#ff6b6b";
    }
  }

  function updatePositions(state) {
    const table = document.querySelector("section .max-h-\\[250px\\], section .flex-1.overflow-y-auto");
    if (!table) return;
    const positions = Array.isArray(state.positions) ? state.positions : [];
    const rows = (positions.length ? positions : (state.holdings || []).map(h => ({
      symbol: `${h.asset}/USDT`, side: "SPOT", contracts: h.amount, markPrice: "-", unrealizedPnl: 0
    }))).slice(0, 12).map(p => {
      const sym = p.symbol || "N/A";
      const side = p.side || p.direction || "N/A";
      const size = (p.contracts ?? p.size ?? 0);
      const mark = (p.markPrice ?? p.mark_price ?? "-");
      const upnl = (p.unrealizedPnl ?? p.unrealized_pnl ?? 0);
      const col = Number(upnl) >= 0 ? "#4edea3" : "#ff6b6b";
      return `<div class="grid grid-cols-8 gap-4 px-md py-sm border-b border-outline-variant items-center">
        <div class="col-span-1 text-on-surface">${sym}</div>
        <div class="col-span-1">${side}</div>
        <div class="col-span-1 text-right">${size}</div>
        <div class="col-span-1 text-right">-</div>
        <div class="col-span-1 text-right">${mark}</div>
        <div class="col-span-1 text-right">-</div>
        <div class="col-span-1 text-right" style="color:${col}">${upnl}</div>
        <div class="col-span-1 text-right"><button data-symbol="${sym}" class="font-label-caps text-label-caps text-primary border border-primary px-3 py-1 rounded-DEFAULT uppercase">Close</button></div>
      </div>`;
    }).join("");
    table.innerHTML = rows;
    bindInteractiveElements();
  }

  function updateLogs(state) {
    const terminal = document.querySelector(".font-data-sm.text-data-sm.flex.flex-col.gap-1.w-full");
    if (!terminal) return;
    const alerts = Array.isArray(state.alerts) ? state.alerts : [];
    const lines = alerts.slice(-18).map(a => {
      const ts = (a.timestamp || "").slice(11,19) || "--:--:--";
      const lvl = (a.level || "INFO").toUpperCase();
      const msg = a.message || "";
      const color = lvl === "ERROR" ? "#ff6b6b" : (lvl === "WARNING" ? "#ffb3ad" : "#8ed5ff");
      return `<div class="flex gap-2"><span class="text-outline w-20 shrink-0">${ts}</span><span style="width:60px;color:${color}" class="shrink-0">[${lvl}]</span><span class="text-on-surface">${msg}</span></div>`;
    }).join("");
    terminal.innerHTML = lines + `<div class="flex gap-2 mt-auto"><span class="text-primary animate-pulse">_</span></div>`;
  }

  function updateAnalytics(state) {
    const spreadVal = document.querySelector("span.font-data-lg.text-display-xl.text-primary-container");
    if (spreadVal && state.btc_last != null && state.eth_last != null) {
      const spread = (Number(state.btc_last) - Number(state.eth_last) / 20);
      spreadVal.textContent = spread.toFixed(5);
    }
  }

  function updateConfiguration(state) {
    const modeToggle = document.querySelector("input[type='checkbox']");
    if (modeToggle) modeToggle.checked = (state.mode || "").includes("TESTNET");
    const keyInput = document.querySelector("input[placeholder='Enter API Key']");
    if (keyInput && state.api_key_masked) keyInput.value = state.api_key_masked;
  }

  async function refreshState() {
    try {
      const res = await fetch("/api/ui-state");
      const state = await res.json();
      setSystemLabel(state.mode, state.system_status);
      if (PAGE === "dashboard") updateDashboard(state);
      if (PAGE === "positions") updatePositions(state);
      if (PAGE === "logs") updateLogs(state);
      if (PAGE === "analytics") updateAnalytics(state);
      if (PAGE === "configuration") updateConfiguration(state);
    } catch (e) {}
  }

  mapNavLinks();
  bindInteractiveElements();
  refreshState();
  setInterval(refreshState, 3000);
})();
</script>
"""


def _render_page(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    if "</body>" in html:
        return html.replace("</body>", INJECT_JS + "\n</body>")
    return html + INJECT_JS


@app.route("/")
def route_root():
    return _render_page(PAGES["dashboard"])


@app.route("/dashboard")
def route_dashboard():
    return _render_page(PAGES["dashboard"])


@app.route("/positions")
def route_positions():
    return _render_page(PAGES["positions"])


@app.route("/analytics")
def route_analytics():
    return _render_page(PAGES["analytics"])


@app.route("/configuration")
def route_configuration():
    return _render_page(PAGES["configuration"])


@app.route("/logs")
def route_logs():
    return _render_page(PAGES["logs"])


@app.route("/favicon.ico")
def route_favicon():
    return ("", 204)


@app.route("/api/ui-state")
def route_state():
    state = runtime.get_state()
    # Add bot status to the state
    bot_status = runtime.get_bot_status()
    state.update({
        "bot_running": bot_status["running"],
        "bot_mode": bot_status["mode"]
    })
    return jsonify(state)


@app.route("/api/ui-action", methods=["POST"])
def route_action():
    payload = request.get_json(silent=True) or {}
    return jsonify(runtime.handle_ui_action(payload))


def _run_server():
    app.run(host="127.0.0.1", port=5050, debug=False, use_reloader=False, threaded=True)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CYBER_BOT_V2 - Exact Design Replica (Python Desktop)")
        self.resize(1500, 920)
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.browser.setUrl(QUrl("http://127.0.0.1:5050/dashboard"))


def main():
    missing = [name for name, path in PAGES.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing design pages: {missing}")

    thread = threading.Thread(target=_run_server, daemon=True)
    thread.start()

    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
