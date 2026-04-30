"""
Design Python App
Serves an exact replica of the `design python` folder and exposes
bot-connected API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging

from flask import Flask, jsonify, abort
from flask_cors import CORS

import config
from data.fetcher import DataFetcher
from execution.broker import Broker
from risk.manager import RiskManager
from data.storage import DataStorage


logger = logging.getLogger(__name__)
app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).parent
DESIGN_SOURCE = PROJECT_ROOT / "design python"

PAGES = {
    "dashboard": DESIGN_SOURCE / "executive_dashboard" / "code.html",
    "positions": DESIGN_SOURCE / "positions_order_book" / "code.html",
    "analytics": DESIGN_SOURCE / "strategy_analytics" / "code.html",
    "configuration": DESIGN_SOURCE / "configuration_settings" / "code.html",
    "logs": DESIGN_SOURCE / "system_logs_monitoring" / "code.html",
    "design_spec": DESIGN_SOURCE / "technical_trading_interface" / "DESIGN.md",
}


def _read_text_file(path: Path) -> str:
    if not path.exists():
        abort(404, description=f"Missing file: {path}")
    return path.read_text(encoding="utf-8")


def _get_live_bot_snapshot() -> Dict[str, Any]:
    """
    Live bot-connected status using existing bot modules.
    Returns graceful fallback values if exchange/data calls fail.
    """
    snapshot: Dict[str, Any] = {
        "running": True,
        "mode": "testnet" if config.TESTNET else "live",
        "exchange": config.EXCHANGE,
        "symbols": config.SYMBOLS,
        "timestamp": datetime.now().isoformat(),
    }

    try:
        broker = Broker(testnet=config.TESTNET)
        balance = broker.fetch_balance()
        usdt_balance = (
            balance.get("total", {}).get("USDT")
            if isinstance(balance, dict)
            else None
        )
        snapshot["balance_usdt"] = usdt_balance
    except Exception as exc:
        logger.warning("Balance fetch failed: %s", exc)
        snapshot["balance_usdt"] = None

    try:
        fetcher = DataFetcher(testnet=config.TESTNET)
        ticker = fetcher.fetch_ticker("BTC/USDT")
        snapshot["btc_last_price"] = ticker.get("last") if isinstance(ticker, dict) else None
    except Exception as exc:
        logger.warning("Ticker fetch failed: %s", exc)
        snapshot["btc_last_price"] = None

    try:
        storage = DataStorage()
        risk = RiskManager(storage)
        snapshot["risk_metrics"] = risk.get_risk_metrics()
    except Exception as exc:
        logger.warning("Risk metrics fetch failed: %s", exc)
        snapshot["risk_metrics"] = {}

    return snapshot


@app.route("/")
def index() -> str:
    return _read_text_file(PAGES["dashboard"])


@app.route("/dashboard")
def dashboard() -> str:
    return _read_text_file(PAGES["dashboard"])


@app.route("/positions")
def positions() -> str:
    return _read_text_file(PAGES["positions"])


@app.route("/analytics")
def analytics() -> str:
    return _read_text_file(PAGES["analytics"])


@app.route("/configuration")
def configuration() -> str:
    return _read_text_file(PAGES["configuration"])


@app.route("/logs")
def logs() -> str:
    return _read_text_file(PAGES["logs"])


@app.route("/api/status")
def api_status():
    return jsonify(
        {
            "status": "online",
            "app": "design_python_app",
            "timestamp": datetime.now().isoformat(),
            "design_source": str(DESIGN_SOURCE),
            "design_source_exists": DESIGN_SOURCE.exists(),
        }
    )


@app.route("/api/design-spec")
def api_design_spec():
    content = _read_text_file(PAGES["design_spec"])
    return jsonify(
        {
            "name": "Technical Trading Interface",
            "path": str(PAGES["design_spec"]),
            "content_preview": content[:1500],
        }
    )


@app.route("/api/components")
def api_components():
    return jsonify(
        [
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "url": f"/{name}" if name != "design_spec" else "/api/design-spec",
            }
            for name, path in PAGES.items()
        ]
    )


@app.route("/api/bot-status")
def api_bot_status():
    return jsonify(_get_live_bot_snapshot())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    app.run(host="127.0.0.1", port=5050, debug=False, threaded=True)
