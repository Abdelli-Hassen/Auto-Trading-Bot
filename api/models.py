from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class StartRequest(BaseModel):
    mode: str = "live"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class BotStatusResponse(BaseModel):
    running: bool
    timestamp: str
    risk_metrics: Dict[str, Any]
    daily_stats: Dict[str, Any]

class TradeResponse(BaseModel):
    timestamp: str
    symbol: str
    side: str
    price: float
    amount: float
    pnl: Optional[float] = None
