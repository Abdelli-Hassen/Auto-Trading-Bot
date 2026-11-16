"""
Runtime-editable settings (risk limits, execution costs, strategy parameters).

Values are validated, applied to the live `config` module and persisted in the
database so they survive restarts. All fractions are stored as fractions
(0.03 = 3%); the UI converts to percentages.
"""
from typing import Any, Dict

import config

# key -> (config attribute, min, max, label, unit)   unit: 'pct' | 'num' | 'int' | 'usd'
RISK_SCHEMA = {
    "max_daily_loss": ("MAX_DAILY_LOSS", 0.001, 0.5, "Max daily loss", "pct"),
    "max_weekly_loss": ("MAX_WEEKLY_LOSS", 0.001, 0.8, "Max weekly loss", "pct"),
    "max_monthly_loss": ("MAX_MONTHLY_LOSS", 0.001, 0.9, "Max monthly loss", "pct"),
    "max_drawdown": ("MAX_DRAWDOWN", 0.01, 0.95, "Max drawdown (halts & liquidates)", "pct"),
    "max_position_size": ("MAX_POSITION_SIZE", 0.01, 1.0, "Max size per coin / leg", "pct"),
    "risk_per_trade": ("RISK_PER_TRADE", 0.001, 0.2, "Risk per pair trade", "pct"),
}
EXEC_SCHEMA = {
    "fee_rate": ("FEE_RATE", 0.0, 0.01, "Fee per fill", "pct"),
    "slippage": ("SLIPPAGE", 0.0, 0.01, "Slippage per fill", "pct"),
    "rebalance_threshold": ("REBALANCE_THRESHOLD", 0.0, 0.2, "Min weight change to rebalance", "pct"),
    "cycle_seconds": ("CYCLE_SECONDS", 2, 3600, "Engine cycle (seconds)", "int"),
    "initial_capital": ("INITIAL_CAPITAL", 100.0, 1e9, "Initial capital (applies on reset)", "usd"),
    "trade_budget_pct": ("TRADE_BUDGET_PCT", 0.01, 1.0, "Trading budget (% of account)", "pct"),
    "trade_budget_usd": ("TRADE_BUDGET_USD", 0.0, 1e9, "Trading budget cap in $ (0 = no cap)", "usd"),
    "trade_size_usd": ("TRADE_SIZE_USD", 0.0, 1e9, "Fixed $ per position (0 = weight-based)", "usd"),
}
STRATEGY_PARAMS = {
    "trend_momentum": {
        "target_vol": {"label": "Volatility target", "min": 0.10, "max": 0.80, "step": 0.05, "unit": "pct", "default": 0.35,
                       "help": "Annualised volatility the portfolio aims for. Lower = smaller positions, smoother ride."},
        "max_position_size": {"label": "Max size per coin", "min": 0.05, "max": 1.0, "step": 0.05, "unit": "pct",
                              "default": 0.30, "help": "Hard cap on a single coin's share of equity."},
        "rebalance_threshold": {"label": "Rebalance threshold", "min": 0.0, "max": 0.2, "step": 0.005, "unit": "pct",
                                "default": 0.02, "help": "Ignore weight changes smaller than this to save fees."},
    },
    "trend_momentum_ls": {
        "target_vol": {"label": "Volatility target", "min": 0.10, "max": 0.80, "step": 0.05, "unit": "pct", "default": 0.35,
                       "help": "Annualised volatility the portfolio aims for. Lower = smaller positions, smoother ride."},
        "max_position_size": {"label": "Max size per coin", "min": 0.05, "max": 1.0, "step": 0.05, "unit": "pct",
                              "default": 0.30, "help": "Hard cap on a single coin's share of equity (long or short)."},
        "rebalance_threshold": {"label": "Rebalance threshold", "min": 0.0, "max": 0.2, "step": 0.005, "unit": "pct",
                                "default": 0.02, "help": "Ignore weight changes smaller than this to save fees."},
    },
    "pairs": {
        "entry_threshold": {"label": "Entry z-score", "min": 1.0, "max": 4.0, "step": 0.1, "unit": "num", "default": 2.0,
                            "help": "Open the pair when the spread is this many std-devs from its mean."},
        "exit_threshold": {"label": "Exit z-score", "min": 0.0, "max": 2.0, "step": 0.1, "unit": "num", "default": 0.5,
                           "help": "Close the pair once the spread has reverted to within this band."},
        "stop_threshold": {"label": "Stop z-score", "min": 2.0, "max": 6.0, "step": 0.1, "unit": "num", "default": 3.0,
                           "help": "Stop out if the spread keeps diverging past this level."},
        "min_edge_mult": {"label": "Min edge vs costs", "min": 0.5, "max": 5.0, "step": 0.1, "unit": "num", "default": 1.5,
                          "help": "Expected profit must be at least this multiple of round-trip costs."},
        "max_position_size": {"label": "Max size per leg", "min": 0.05, "max": 1.0, "step": 0.05, "unit": "pct",
                              "default": 0.30, "help": "Share of equity allocated to each leg."},
    },
}
PARAM_TARGETS = {          # strategy param -> config attribute (global ones)
    "max_position_size": "MAX_POSITION_SIZE", "rebalance_threshold": "REBALANCE_THRESHOLD",
    "entry_threshold": "ENTRY_THRESHOLD", "exit_threshold": "EXIT_THRESHOLD",
    "stop_threshold": "STOP_THRESHOLD", "min_edge_mult": "MIN_EDGE_MULT",
}


def current_values() -> Dict[str, Dict[str, Any]]:
    out = {"risk": {}, "execution": {}}
    for k, (attr, *_rest) in RISK_SCHEMA.items():
        out["risk"][k] = getattr(config, attr)
    for k, (attr, *_rest) in EXEC_SCHEMA.items():
        out["execution"][k] = getattr(config, attr)
    return out


def schema() -> Dict[str, Any]:
    def conv(s):
        return {k: {"label": v[3], "min": v[1], "max": v[2], "unit": v[4]} for k, v in s.items()}
    return {"risk": conv(RISK_SCHEMA), "execution": conv(EXEC_SCHEMA)}


def validate(group_schema: Dict, values: Dict[str, Any]) -> Dict[str, float]:
    clean = {}
    for key, val in (values or {}).items():
        if key not in group_schema:
            raise ValueError(f"Unknown setting: {key}")
        _, lo, hi, label, unit = group_schema[key]
        try:
            num = float(val)
        except (TypeError, ValueError):
            raise ValueError(f"{label}: not a number")
        if not (lo <= num <= hi):
            raise ValueError(f"{label} must be between {lo} and {hi}")
        clean[key] = int(num) if unit == "int" else num
    return clean


def apply_global(risk: Dict[str, float] = None, execution: Dict[str, float] = None):
    for k, v in (risk or {}).items():
        setattr(config, RISK_SCHEMA[k][0], v)
    for k, v in (execution or {}).items():
        setattr(config, EXEC_SCHEMA[k][0], v)
