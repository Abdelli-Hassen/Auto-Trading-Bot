"""
Repair a paper account that was corrupted by bad price data.

What it does (run with the API stopped):
  1. finds fills whose price is more than 50% away from the previous good fill of the same coin
     (e.g. a simulated $103 "DOGE" price after a real $0.06 one) and deletes them
  2. deletes equity-history points that collapsed below 50% of starting capital
  3. rebuilds cash/positions/fees by replaying the remaining fills through the paper account
  4. drops "closed trade" records that were produced by the bad fills

Usage:  python tools/repair_account.py [path/to/trading_data.db]  [--apply]
Without --apply it only reports what it would change.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402
from execution.paper import PaperAccount  # noqa: E402

THRESHOLD = 0.5


def find_corrupt(rows):
    """rows: (id, symbol, price[, timestamp]). Corrupt fills = price >50% away from the last good price of that coin,
    plus every fill of the same liquidation burst (within 2 minutes), since they used the same bad feed."""
    from datetime import datetime
    last, bad, burst_until = {}, [], None
    for row in rows:
        id_, sym, price = row[0], row[1], row[2]
        ts = datetime.fromisoformat(row[3]) if len(row) > 3 and row[3] else None
        ref = last.get(sym)
        if ref and price and abs(price / ref - 1) > THRESHOLD:
            bad.append(id_)
            burst_until = ts.timestamp() + 120 if ts else None
        elif burst_until and ts and ts.timestamp() <= burst_until:
            bad.append(id_)                                   # same burst, same bad feed
        elif price:
            last[sym] = price
    return bad


def replay(fills, initial, fee_rate, slippage):
    """Rebuild a PaperAccount from stored fills (fill prices already include slippage)."""
    acct = PaperAccount(initial, fee_rate=fee_rate, slippage=slippage)
    for f in fills:
        sym, side, amount, fill_price = f["symbol"], f["side"], f["amount"], f["price"]
        raw = fill_price / (1 + slippage) if side == "buy" else fill_price / (1 - slippage)
        pos = acct.positions.get(sym)
        if pos is None:
            acct._resize(sym, "long" if side == "buy" else "short", amount, raw)
        else:
            grows = (side == "buy") == (pos["side"] == "long")
            new_size = pos["size"] + amount if grows else pos["size"] - amount
            if new_size < -1e-9:                                   # flipped through zero
                acct._resize(sym, pos["side"], 0.0, raw)
                acct._resize(sym, "long" if side == "buy" else "short", -new_size, raw)
            else:
                acct._resize(sym, pos["side"], max(new_size, 0.0), raw)
        if sym in acct.positions:
            acct.positions[sym]["mark_price"] = raw
    return acct


def main(db_path, apply=False):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, symbol, price, timestamp FROM trades ORDER BY id").fetchall()
    bad = find_corrupt(rows)
    print(f"{len(rows)} fills, {len(bad)} corrupt: {bad}")
    st_row = conn.execute("SELECT value FROM state WHERE key='paper_account'").fetchone()
    settings_row = conn.execute("SELECT value FROM state WHERE key='settings'").fetchone()
    settings = json.loads(settings_row[0]) if settings_row else {}
    initial = float(settings.get("execution", {}).get("initial_capital", config.INITIAL_CAPITAL))
    fee = float(settings.get("execution", {}).get("fee_rate", config.FEE_RATE))
    slip = float(settings.get("execution", {}).get("slippage", config.SLIPPAGE))

    good = conn.execute(
        "SELECT id, symbol, side, amount, price FROM trades WHERE id NOT IN (%s) ORDER BY id" %
        (",".join(map(str, bad)) or "-1")).fetchall()
    fills = [dict(id=i, symbol=s, side=sd, amount=a, price=p) for i, s, sd, a, p in good]
    acct = replay(fills, initial, fee, slip)
    bad_equity = conn.execute("SELECT COUNT(*) FROM equity WHERE equity < ?", (initial * 0.5,)).fetchone()[0]
    print(f"rebuilt account: cash {acct.cash:,.2f}, {len(acct.positions)} positions, fees {acct.fees_paid:,.2f}, "
          f"realised {acct.realized_pnl:,.2f}; deleting {bad_equity} bad equity points")

    if not apply:
        print("(dry run - nothing changed; add --apply)")
        return acct
    state = json.loads(st_row[0]) if st_row else {}
    state.update({"cash": acct.cash, "positions": acct.positions, "fees_paid": acct.fees_paid,
                  "realized_pnl": acct.realized_pnl})
    state["pair_trades"] = [t for t in state.get("pair_trades", []) if abs(t.get("pnl", 0)) < initial * 0.25]
    conn.execute("DELETE FROM trades WHERE id IN (%s)" % (",".join(map(str, bad)) or "-1"))
    conn.execute("DELETE FROM equity WHERE equity < ?", (initial * 0.5,))
    conn.execute("INSERT OR REPLACE INTO state (key, value) VALUES ('paper_account', ?)", (json.dumps(state, default=str),))
    conn.commit()
    conn.close()
    print("repaired.")
    return acct


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else str(config.DATA_DIR / "storage" / "trading_data.db")
    main(path, apply="--apply" in sys.argv)
