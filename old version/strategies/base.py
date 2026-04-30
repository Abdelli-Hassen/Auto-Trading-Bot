import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import config
from utils import setup_logger

logger = setup_logger("StrategyBase", "strategy.log")

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.parameters = {}
        self.logger = setup_logger(f"Strategy.{name}", f"strategy_{name}.log")
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from market data.
        Should return DataFrame with columns: ['signal', 'entry_price', 'stop_loss', 'take_profit']
        Signal values: 1 (long), -1 (short), 0 (no position)
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, signal: Dict, account_balance: float) -> float:
        """
        Calculate position size for a given signal.
        """
        pass
    
    def validate_signal(self, signal: Dict) -> bool:
        """
        Validate that a signal contains all required information.
        """
        required_fields = ['signal', 'entry_price']
        for field in required_fields:
            if field not in signal:
                self.logger.warning(f"Missing required field in signal: {field}")
                return False
        
        if signal['signal'] not in [-1, 0, 1]:
            self.logger.warning(f"Invalid signal value: {signal['signal']}")
            return False
            
        if signal['signal'] != 0 and signal['entry_price'] <= 0:
            self.logger.warning(f"Invalid entry price for non-zero signal: {signal['entry_price']}")
            return False
            
        return True
    
    def set_parameters(self, params: Dict):
        """Set strategy parameters."""
        self.parameters.update(params)
        self.logger.info(f"Strategy parameters updated: {self.parameters}")
    
    def get_parameters(self) -> Dict:
        """Get current strategy parameters."""
        return self.parameters.copy()
