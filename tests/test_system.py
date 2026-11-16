import asyncio

import numpy as np
import pandas as pd
import pytest

import config
from backtest.engine import BacktestEngine
from execution.paper import PaperAccount
from main import TradingBot
from strategies.pairs_trading import PairsTradingStrategy


# ---------------------------------------------------------------- paper account
def test_long_roundtrip_pnl_and_fees():
    a = PaperAccount(10000, fee_rate=0.001, slippage=0.0)
    a.open_position("BTC/USDT", "long", 1.0, 100.0)
    a.mark({"BTC/USDT": 110.0})
    assert a.unrealized_pnl() == pytest.approx(10.0)
    fill = a.close_position("BTC/USDT", 110.0)
    assert fill["pnl"] == pytest.approx(10 - 0.1 - 0.11)   # gross minus both fees
    assert a.equity() == pytest.approx(10000 + fill["pnl"])
    assert not a.positions


def test_short_profits_when_price_falls():
    a = PaperAccount(10000, fee_rate=0.0, slippage=0.0)
    a.open_position("ETH/USDT", "short", 2.0, 50.0)
    fill = a.close_position("ETH/USDT", 40.0)
    assert fill["pnl"] == pytest.approx(20.0)


def test_slippage_hurts_both_sides():
    a = PaperAccount(10000, fee_rate=0.0, slippage=0.01)
    a.open_position("BTC/USDT", "long", 1.0, 100.0)
    fill = a.close_position("BTC/USDT", 100.0)
    assert fill["pnl"] < 0


def test_rejects_invalid_orders_and_duplicates():
    a = PaperAccount(1000)
    assert a.open_position("X", "long", 0, 10) is None
    assert a.open_position("X", "long", 1, 10) is not None
    assert a.open_position("X", "long", 1, 10) is None
    assert a.close_position("NOPE", 10) is None


# -------------------------------------------------------------------- strategy
def test_decide_state_machine():
    s = PairsTradingStrategy()
    assert s.decide(-2.5, None) == "open_long"
    assert s.decide(2.5, None) == "open_short"
    assert s.decide(1.0, None) == "hold"
    assert s.decide(0.2, "long") == "close"
    assert s.decide(-3.5, "long") == "stop"
    assert s.decide(3.5, "short") == "stop"
    assert s.decide(-1.5, "long") == "hold"


def test_rolling_zscore_detects_divergence():
    rng = np.random.default_rng(1)
    base = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, 200)))
    p2 = pd.Series(base)
    p1 = pd.Series(base * 20 * np.exp(rng.normal(0, 0.001, 200)))
    p1.iloc[-1] *= 1.05
    z = PairsTradingStrategy().rolling_zscore(p1, p2)["z"]
    assert z.iloc[-1] > 3


# -------------------------------------------------------------------- backtest
def test_backtest_runs_and_is_consistent(fetcher):
    s = PairsTradingStrategy()
    engine = BacktestEngine(10000, fetcher)
    a = fetcher.synthetic.ohlcv("BTC/USDT", "1m", 900)
    b = fetcher.synthetic.ohlcv("ETH/USDT", "1m", 900)
    frame = pd.DataFrame({"timestamp": a["timestamp"], "close_1": a["close"], "close_2": b["close"]})
    r = engine.run_on_frame(s, frame, "1m")
    assert r["total_trades"] > 0
    assert r["final_capital"] == pytest.approx(r["equity_curve"][-1][1])
    assert 0 <= r["max_drawdown"] <= 1
    assert r["winning_trades"] + r["losing_trades"] == r["total_trades"]


# ------------------------------------------------------------------- live bot
def make_bot(storage, fetcher):
    return TradingBot(storage=storage, data_fetcher=fetcher)


def test_cycle_opens_and_closes_pair(storage, fetcher):
    bot = make_bot(storage, fetcher)
    s1, s2 = bot.strategy.pair
    bot._open_pair(True, {s1: 65000.0, s2: 3200.0}, -2.4)
    pos = bot.account.positions
    assert pos[s1]["side"] == "long" and pos[s2]["side"] == "short"
    n1 = pos[s1]["size"] * 65000
    n2 = pos[s2]["size"] * 3200
    assert n1 == pytest.approx(n2, rel=0.01)                      # dollar neutral
    assert n1 == pytest.approx(config.INITIAL_CAPITAL * config.MAX_POSITION_SIZE, rel=0.01)
    bot._close_pair({s1: 65500.0, s2: 3180.0}, "mean_reversion", 0.1)
    assert not bot.account.positions
    assert len(bot.pair_trades) == 1 and bot.pair_trades[0]["pnl"] > 0
    assert len(bot.recent_signals) == 2


def test_state_persists_across_restart(storage, fetcher):
    bot = make_bot(storage, fetcher)
    s1, s2 = bot.strategy.pair
    bot._open_pair(False, {s1: 65000.0, s2: 3200.0}, 2.4)
    bot._save_state()
    again = make_bot(storage, fetcher)
    assert set(again.account.positions) == {s1, s2}
    assert again.account.cash == pytest.approx(bot.account.cash)


def test_liquidate_and_reset(storage, fetcher):
    bot = make_bot(storage, fetcher)
    s1, s2 = bot.strategy.pair
    bot._open_pair(True, {s1: 65000.0, s2: 3200.0}, -2.4)
    out = bot.liquidate()
    assert out["closed"] == 2 and not bot.account.positions
    assert bot.liquidate()["closed"] == 0
    bot.reset()
    assert bot.account.equity() == config.INITIAL_CAPITAL
    assert bot.pair_trades == []


def test_live_loop_runs_cycles(storage, fetcher, monkeypatch):
    monkeypatch.setattr(config, "CYCLE_SECONDS", 0)
    bot = make_bot(storage, fetcher)
    bot.portfolio_mode = False      # exercise the pairs loop

    async def run():
        task = asyncio.create_task(bot.run_live_mode())
        await asyncio.sleep(2.5)
        bot.stop()
        await asyncio.wait_for(task, 5)

    asyncio.run(run())
    assert bot.last_cycle is not None
    assert bot.pair_stats.get("ready")
    assert storage.get_stats()["equity_records"] >= 1
    assert bot.account.equity() == pytest.approx(bot.account.cash + bot.account.unrealized_pnl())


def test_risk_limits_block_entries(storage, fetcher):
    bot = make_bot(storage, fetcher)
    bot.risk_manager.record_pnl(-config.INITIAL_CAPITAL * config.MAX_DAILY_LOSS * 1.1)
    ok, reason = bot.risk_manager.can_open_new_position("BTC/USDT", [])
    assert not ok and "Daily" in reason


# ------------------------------------------------------------------------- api
def test_api_endpoints(tmp_path, monkeypatch, fetcher):
    from fastapi.testclient import TestClient
    from api import server
    from data.storage import DataStorage

    bot = TradingBot(storage=DataStorage(tmp_path / "api.db"), data_fetcher=fetcher)
    monkeypatch.setattr(server, "bot_instance", bot)
    with TestClient(server.app) as c:
        assert c.get("/api/health").json()["mode"] == "paper"
        st = c.get("/api/status").json()
        assert st["risk_metrics"]["current_equity"] == config.INITIAL_CAPITAL
        assert c.get("/api/status/balance").json()["USDT"]["free"] == config.INITIAL_CAPITAL
        assert len(c.get("/api/test/ohlcv?symbol=BTC/USDT&timeframe=1m&limit=50").json()) == 50
        assert c.get("/api/test/history").json() == []
        assert len(c.get("/api/test/analytics").json()["metrics"]) == 6
        assert c.post("/api/bot/liquidate").json()["status"] == "success"
        assert c.post("/api/bot/stop").json()["status"] == "error"
        with c.websocket_connect("/ws/stream") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "update" and "BTC/USDT" in msg["prices"]
        r = c.post("/api/backtest",
                   json={"start_date": "2024-01-01", "end_date": "2024-02-01", "timeframe": "1m"}).json()
        assert r["status"] in ("success", "error")
        assert c.post("/api/bot/reset").json()["status"] == "success"


# ------------------------------------------------------- trend/momentum portfolio
def _prices(n=1500, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-01", periods=n, freq="4h")
    common = rng.normal(0.0004, 0.01, n)
    from strategies.trend_momentum import COINS
    return pd.DataFrame({c: 100 * np.exp(np.cumsum(common + rng.normal(0, 0.008, n))) for c in COINS}, index=idx)


def test_portfolio_weights_are_long_only_and_unlevered():
    from strategies.trend_momentum import TrendMomentumStrategy
    w = TrendMomentumStrategy().compute_weights(_prices())
    assert (w >= 0).all().all()
    assert w.sum(axis=1).max() <= 1.0 + 1e-9
    assert w.max().max() <= config.MAX_POSITION_SIZE + 1e-9


def test_portfolio_has_no_lookahead():
    from strategies.trend_momentum import TrendMomentumStrategy
    s, P = TrendMomentumStrategy(), _prices()
    full = s.compute_weights(P)
    part = s.compute_weights(P.iloc[:1200])
    pd.testing.assert_frame_equal(full.iloc[:1200], part, check_exact=False, atol=1e-9)


def test_set_long_size_partial_and_full_close():
    a = PaperAccount(10000, fee_rate=0.0, slippage=0.0)
    a.set_long_size("X", 10, 100.0)
    a.set_long_size("X", 20, 110.0)                       # add: avg entry 105
    assert a.positions["X"]["entry_price"] == pytest.approx(105.0)
    f = a.set_long_size("X", 10, 120.0)                   # reduce by 10
    assert f["pnl"] == pytest.approx(150.0) and not f["closed"]
    f = a.set_long_size("X", 0, 120.0)
    assert f["closed"] and "X" not in a.positions
    assert a.equity() == pytest.approx(10000 + a.realized_pnl)


def test_portfolio_rebalance_buys_and_exits(storage, fetcher):
    bot = make_bot(storage, fetcher)
    prices = {s: 100.0 for s in bot.portfolio_strategy.symbols}
    bot.target_weights = {s: 0.0 for s in prices}
    bot.target_weights["BTC/USDT"] = 0.3
    bot.target_weights["ETH/USDT"] = 0.2
    bot._rebalance(prices)
    assert bot.account.positions["BTC/USDT"]["size"] * 100 == pytest.approx(0.3 * config.INITIAL_CAPITAL, rel=0.01)
    assert bot.account.exposure() <= bot.account.equity()
    bot.target_weights["ETH/USDT"] = 0.0
    bot._rebalance({**prices, "ETH/USDT": 110.0})
    assert "ETH/USDT" not in bot.account.positions
    assert len(bot.pair_trades) == 1 and bot.pair_trades[0]["pnl"] > 0


def test_portfolio_cycle_end_to_end(storage, fetcher):
    bot = make_bot(storage, fetcher)
    asyncio.run(bot._portfolio_cycle())
    assert bot.last_cycle is not None
    assert bot._last_bar is not None and bot.target_weights
    assert sum(bot.target_weights.values()) <= 1.0 + 1e-9
    st = bot.get_status()
    assert st["strategy"] == "TrendMomentum" and "weights" in st["portfolio"]


# ------------------------------------------------- strategies / settings / status API
def test_strategy_settings_and_status_api(tmp_path, monkeypatch, fetcher):
    from fastapi.testclient import TestClient
    from api import server
    from data.storage import DataStorage

    bot = TradingBot(storage=DataStorage(tmp_path / "api2.db"), data_fetcher=fetcher)
    monkeypatch.setattr(server, "bot_instance", bot)
    with TestClient(server.app) as c:
        cards = c.get("/api/strategies").json()
        assert {s["id"] for s in cards} == {"trend_momentum", "trend_momentum_ls", "pairs"}
        trend = next(s for s in cards if s["id"] == "trend_momentum")
        assert trend["selected"] and trend["stats"]["win_rate"] is None       # no fake win rate
        assert {p["key"] for p in trend["params"]} >= {"target_vol", "max_position_size"}

        # parameters: validated, applied and persisted
        assert c.put("/api/strategies/trend_momentum/params", json={"params": {"target_vol": 0.5}}).json()["status"] == "success"
        assert bot.portfolio_strategy.target_vol == 0.5
        assert c.put("/api/strategies/trend_momentum/params", json={"params": {"target_vol": 9}}).json()["status"] == "error"
        assert c.put("/api/strategies/trend_momentum/params", json={"params": {"nope": 1}}).json()["status"] == "error"
        reloaded = TradingBot(storage=bot.storage, data_fetcher=fetcher)
        assert reloaded.portfolio_strategy.target_vol == 0.5

        # settings
        assert c.put("/api/settings", json={"risk": {"max_daily_loss": 0.04}}).json()["status"] == "success"
        assert config.MAX_DAILY_LOSS == 0.04
        assert c.put("/api/settings", json={"risk": {"max_daily_loss": 7}}).json()["status"] == "error"
        assert reloaded.risk_manager.get_risk_metrics()["limits"]["daily"] == 0.04
        config.MAX_DAILY_LOSS = 0.03

        # strategy switching is blocked while positions are open
        s1, s2 = bot.strategy.pair
        bot.account.set_long_size("BTC/USDT", 1.0, 100.0)
        assert c.post("/api/strategies/pairs/select").json()["status"] == "error"
        bot.account.close_position("BTC/USDT", 100.0)
        assert c.post("/api/strategies/pairs/select").json()["status"] == "success"
        assert bot.strategy_id == "pairs"
        assert c.post("/api/strategies/trend_momentum/select").json()["status"] == "success"

        # status is fully populated for the UI
        st = c.get("/api/status").json()
        for key in ("summary", "scan", "events", "portfolio", "strategy_id", "alerts_last_id"):
            assert key in st
        assert st["daily_stats"]["win_rate"] is None
        assert c.get("/api/account").json()["mode"] == "paper"
        with c.websocket_connect("/ws/stream") as ws:       # snapshot arrives immediately
            assert ws.receive_json()["status"]["strategy_id"] == "trend_momentum"


# ------------------------------------------------------------ long/short portfolio
def test_signed_resize_flips_and_pnl_direction():
    a = PaperAccount(10000, fee_rate=0.0, slippage=0.0)
    a.set_signed_size("X", -10, 100.0)                       # open short
    assert a.positions["X"]["side"] == "short"
    fills = a.set_signed_size("X", -5, 90.0)                 # cover half at a profit
    assert fills[0]["pnl"] == pytest.approx(50.0) and not fills[0]["closed"]
    fills = a.set_signed_size("X", 4, 90.0)                  # flip to long: close short, open long
    assert [f["action"] for f in fills] == ["close", "open"]
    assert a.positions["X"]["side"] == "long"
    assert a.realized_pnl == pytest.approx(100.0)


def test_long_short_weights_respect_gross_limit_and_can_short():
    from strategies.trend_momentum import TrendMomentumStrategy
    rng = np.random.default_rng(5)
    from strategies.trend_momentum import COINS
    n = 1500
    idx = pd.date_range("2023-01-01", periods=n, freq="4h")
    P = pd.DataFrame({c: 100 * np.exp(np.cumsum(rng.normal(-0.002, 0.01, n))) for c in COINS}, index=idx)   # bear market
    w = TrendMomentumStrategy(allow_shorts=True).compute_weights(P)
    assert w.abs().sum(axis=1).max() <= 1.0 + 1e-9
    assert (w < 0).any().any()                                # it shorts in a falling market
    assert not (TrendMomentumStrategy().compute_weights(P) < 0).any().any()      # long-only never does


def test_portfolio_rebalance_with_shorts(storage, fetcher):
    bot = make_bot(storage, fetcher)
    bot.strategy_id = "trend_momentum_ls"
    prices = {s: 100.0 for s in bot.portfolio_strategy.symbols}
    bot.target_weights = {s: 0.0 for s in prices}
    bot.target_weights["BTC/USDT"] = -0.2
    bot._rebalance(prices)
    pos = bot.account.positions["BTC/USDT"]
    assert pos["side"] == "short" and pos["size"] * 100 == pytest.approx(0.2 * config.INITIAL_CAPITAL, rel=0.01)
    bot._rebalance({**prices, "BTC/USDT": 90.0}) if False else None
    bot.target_weights["BTC/USDT"] = 0.0
    bot._rebalance({**prices, "BTC/USDT": 90.0})
    assert "BTC/USDT" not in bot.account.positions
    assert bot.pair_trades[-1]["pnl"] > 0 and bot.pair_trades[-1]["strategy"] == "trend_momentum_ls"


# ------------------------------------------------------------- trading budget & funds
def test_trading_budget_scales_positions(storage, fetcher, monkeypatch):
    monkeypatch.setattr(config, "TRADE_BUDGET_PCT", 0.5)
    bot = make_bot(storage, fetcher)
    assert bot.trading_base() == pytest.approx(0.5 * config.INITIAL_CAPITAL)
    prices = {s: 100.0 for s in bot.portfolio_strategy.symbols}
    bot.target_weights = {s: 0.0 for s in prices}
    bot.target_weights["BTC/USDT"] = 0.3
    bot._rebalance(prices)
    assert bot.account.positions["BTC/USDT"]["size"] * 100 == pytest.approx(0.3 * 0.5 * config.INITIAL_CAPITAL, rel=0.01)
    monkeypatch.setattr(config, "TRADE_BUDGET_USD", 2000.0)               # dollar cap wins when smaller
    assert bot.trading_base() == 2000.0


def test_deposit_withdraw_keep_pnl_and_drawdown_clean(storage, fetcher):
    bot = make_bot(storage, fetcher)
    start = config.INITIAL_CAPITAL
    bot.deposit(5000)
    assert bot.account.equity() == pytest.approx(start + 5000)
    assert bot.risk_manager.get_risk_metrics()["total_pnl"] == pytest.approx(0.0)       # deposits are not profit
    bot.withdraw(2000)
    m = bot.risk_manager.get_risk_metrics()
    assert m["total_pnl"] == pytest.approx(0.0) and m["current_drawdown"] == pytest.approx(0.0)   # not a fake drawdown
    with pytest.raises(ValueError):
        bot.withdraw(1e7)
    with pytest.raises(ValueError):
        bot.deposit(-5)
    # funds in positions cannot be withdrawn
    bot.account.set_long_size("BTC/USDT", 20.0, 100.0)                  # $2,000 deployed
    assert bot.free_funds() == pytest.approx(bot.account.equity() - 2000, rel=0.01)
    with pytest.raises(ValueError):
        bot.withdraw(bot.account.equity())


def test_funds_and_budget_api(tmp_path, monkeypatch, fetcher):
    from fastapi.testclient import TestClient
    from api import server
    from data.storage import DataStorage
    bot = TradingBot(storage=DataStorage(tmp_path / "f.db"), data_fetcher=fetcher)
    monkeypatch.setattr(server, "bot_instance", bot)
    with TestClient(server.app) as c:
        assert c.post("/api/account/deposit", json={"amount": 1000}).json()["status"] == "success"
        assert c.post("/api/account/withdraw", json={"amount": 99999999}).json()["status"] == "error"
        r = c.put("/api/settings", json={"execution": {"trade_budget_pct": 0.25}}).json()
        assert r["status"] == "success"
        cap = c.get("/api/status").json()["capital"]
        assert cap["budget"] == pytest.approx(0.25 * cap["equity"])
        assert c.put("/api/settings", json={"execution": {"trade_budget_pct": 5}}).json()["status"] == "error"
        config.TRADE_BUDGET_PCT = 1.0
        reloaded = TradingBot(storage=bot.storage, data_fetcher=fetcher)
        assert reloaded.account.initial_capital == pytest.approx(config.INITIAL_CAPITAL)


def test_fixed_amount_per_trade(storage, fetcher, monkeypatch):
    monkeypatch.setattr(config, "TRADE_SIZE_USD", 100.0)
    bot = make_bot(storage, fetcher)
    bot.strategy_id = "trend_momentum_ls"
    prices = {s: 50.0 for s in bot.portfolio_strategy.symbols}
    bot.target_weights = {s: 0.0 for s in prices}
    bot.target_weights.update({"BTC/USDT": 0.3, "ETH/USDT": -0.05, "SOL/USDT": 0.1})     # very different weights
    bot._rebalance(prices)
    for sym, side in (("BTC/USDT", "long"), ("ETH/USDT", "short"), ("SOL/USDT", "long")):
        pos = bot.account.positions[sym]
        assert pos["side"] == side and pos["size"] * 50.0 == pytest.approx(100.0, rel=0.01)     # exactly $100 each
    assert bot.account.exposure() == pytest.approx(300.0, rel=0.01)
    bot._rebalance(prices)                                                  # idempotent: no churn
    assert len(bot.order_manager.get_order_history()) == 3
    monkeypatch.setattr(config, "TRADE_SIZE_USD", 1e7)                       # larger than the budget -> scaled down
    bot._rebalance(prices)
    assert bot.account.exposure() <= bot.trading_base() * 1.001


def test_pnl_breakdown_adds_up_and_today_includes_open(storage, fetcher):
    bot = make_bot(storage, fetcher)
    bot.account.set_long_size("BTC/USDT", 10.0, 100.0)
    bot.account.mark({"BTC/USDT": 105.0})
    bot.account.set_long_size("BTC/USDT", 5.0, 105.0)            # lock in part of the gain
    bot.account.mark({"BTC/USDT": 103.0})
    st = bot.get_status()
    acct = st["account"]
    total = st["risk_metrics"]["total_pnl"]
    # locked-in + open - fees == total P&L
    assert acct["realised_gross"] + acct["open_pnl"] - acct["fees_paid"] == pytest.approx(total)
    assert st["daily_stats"]["pnl"] == pytest.approx(total)      # nothing else happened today
    bot.deposit(1000)
    assert bot.get_status()["daily_stats"]["pnl"] == pytest.approx(total)    # deposits are not profit


def test_today_is_measured_from_midnight_using_history(storage, fetcher):
    conn = storage.get_connection()
    conn.execute("INSERT INTO equity (timestamp, equity, balance) VALUES ('2000-01-01 12:00:00', 10000, 10000)")
    conn.commit()
    conn.close()
    bot = make_bot(storage, fetcher)
    bot.account.cash += 50                                   # +$50 earned today
    st = bot.get_status()
    assert st["daily_stats"]["pnl"] == pytest.approx(50.0)
    assert st["daily_stats"]["pnl"] == pytest.approx(st["risk_metrics"]["total_pnl"])
