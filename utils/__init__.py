import logging
import os
from pathlib import Path
from datetime import datetime
import json

# Design manager imports
from .design_manager import (
    DesignManager,
    get_design_manager,
    initialize_design_manager,
)

BASE_DIR = Path(__file__).parent.parent

def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        log_path = BASE_DIR / "logs" / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def load_json(path: Path) -> dict:
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_json(path: Path, data: dict):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def format_currency(value: float) -> str:
    return f"${value:,.2f}"

def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"

def calculate_sharpe(returns: list, risk_free_rate: float = 0.0) -> float:
    if not returns or len(returns) < 2:
        return 0.0
    import numpy as np
    returns = np.array(returns)
    excess_returns = returns - risk_free_rate
    if np.std(excess_returns) == 0:
        return 0.0
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

def calculate_max_drawdown(equity_curve: list) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak
        if dd > max_dd:
            max_dd = dd
    return max_dd

def calculate_profit_factor(trades: list) -> float:
    if not trades:
        return 0.0
    wins = sum(t for t in trades if t > 0)
    losses = abs(sum(t for t in trades if t < 0))
    if losses == 0:
        return float('inf') if wins > 0 else 0.0
    return wins / losses