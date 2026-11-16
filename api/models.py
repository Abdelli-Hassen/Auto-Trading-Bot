from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class StartRequest(BaseModel):
    mode: str = "live"
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class FundsRequest(BaseModel):
    amount: float


class ParamsRequest(BaseModel):
    params: Dict[str, float]


class SettingsRequest(BaseModel):
    risk: Dict[str, float] = {}
    execution: Dict[str, float] = {}


class BacktestRequest(BaseModel):
    start_date: str
    end_date: str
    timeframe: str = "1h"


class BotStatusResponse(BaseModel):
    running: bool
    timestamp: str
    risk_metrics: Dict[str, Any]
    daily_stats: Dict[str, Any]
    mode: str = "paper"
    data_source: str = "exchange"
    recent_signals: List[Dict[str, Any]] = []
    prediction: Dict[str, Any] = {}
    pair: Dict[str, Any] = {}
    positions: List[Dict[str, Any]] = []
    account: Dict[str, Any] = {}
    last_cycle: Optional[str] = None
    strategy: str = ""
    capital: Dict[str, Any] = {}
    started_at: Optional[str] = None
    strategy_id: str = ""
    summary: str = ""
    scan: Dict[str, Any] = {}
    analysis_at: Optional[str] = None
    next_bar_seconds: Optional[int] = None
    events: List[Dict[str, Any]] = []
    alerts_last_id: int = 0
    portfolio: Dict[str, Any] = {}
