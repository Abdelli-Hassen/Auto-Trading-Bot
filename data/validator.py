import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import config
from utils import setup_logger

logger = setup_logger("DataValidator", "validation.log")

class DataValidator:
    def __init__(self):
        pass
    
    def validate_ohlcv(self, df: pd.DataFrame, symbol: str = None) -> Tuple[bool, List[str]]:
        errors = []
        
        if df.empty:
            errors.append("DataFrame is empty")
            return False, errors
        
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing columns: {missing_columns}")
            return False, errors
        
        if df['timestamp'].isnull().any():
            errors.append("Timestamp contains null values")
        
        if (df['open'] <= 0).any():
            errors.append("Open price contains zero or negative values")
        
        if (df['high'] <= 0).any():
            errors.append("High price contains zero or negative values")
        
        if (df['low'] <= 0).any():
            errors.append("Low price contains zero or negative values")
        
        if (df['close'] <= 0).any():
            errors.append("Close price contains zero or negative values")
        
        if (df['volume'] < 0).any():
            errors.append("Volume contains negative values")
        
        high_low_check = (df['high'] >= df['low']).all()
        if not high_low_check:
            errors.append("High price is less than low price in some rows")
        
        high_open_close_check = ((df['high'] >= df['open']) & (df['high'] >= df['close'])).all()
        if not high_open_close_check:
            errors.append("High price is less than open or close in some rows")
        
        low_open_close_check = ((df['low'] <= df['open']) & (df['low'] <= df['close'])).all()
        if not low_open_close_check:
            errors.append("Low price is greater than open or close in some rows")
        
        price_jumps = self._detect_price_jumps(df)
        if price_jumps:
            errors.append(f"Unusual price jumps detected in {len(price_jumps)} rows")
        
        volume_spikes = self._detect_volume_spikes(df)
        if volume_spikes:
            errors.append(f"Unusual volume spikes detected in {len(volume_spikes)} rows")
        
        timestamp_issues = self._check_timestamps(df)
        if timestamp_issues:
            errors.append(f"Timestamp issues: {timestamp_issues}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _detect_price_jumps(self, df: pd.DataFrame, threshold: float = 0.1) -> List[int]:
        jumps = []
        if len(df) < 2:
            return jumps
        
        df_sorted = df.sort_values('timestamp').reset_index(drop=True)
        price_changes = df_sorted['close'].pct_change().abs()
        
        jump_indices = price_changes[price_changes > threshold].index.tolist()
        return jump_indices
    
    def _detect_volume_spikes(self, df: pd.DataFrame, threshold: float = 5.0) -> List[int]:
        spikes = []
        if len(df) < 2:
            return spikes
        
        df_sorted = df.sort_values('timestamp').reset_index(drop=True)
        volume_median = df_sorted['volume'].median()
        if volume_median == 0:
            return spikes
        
        volume_ratio = df_sorted['volume'] / volume_median
        spike_indices = volume_ratio[volume_ratio > threshold].index.tolist()
        return spike_indices
    
    def _check_timestamps(self, df: pd.DataFrame) -> List[str]:
        issues = []
        if len(df) < 2:
            return issues
        
        df_sorted = df.sort_values('timestamp').reset_index(drop=True)
        time_diffs = df_sorted['timestamp'].diff().dt.total_seconds()
        
        expected_interval = 60  # 1 minute in seconds
        
        gap_threshold = expected_interval * 3
        gaps = time_diffs[time_diffs > gap_threshold]
        if len(gaps) > 0:
            issues.append(f"{len(gaps)} time gaps > {gap_threshold}s")
        
        duplicates = df_sorted['timestamp'].duplicated()
        if duplicates.any():
            issues.append(f"{duplicates.sum()} duplicate timestamps")
        
        return issues
    
    def validate_trade(self, trade: Dict) -> Tuple[bool, List[str]]:
        errors = []
        
        required_fields = ['symbol', 'side', 'type', 'amount', 'price']
        for field in required_fields:
            if field not in trade:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        if trade['side'] not in ['buy', 'sell']:
            errors.append(f"Invalid side: {trade['side']}")
        
        if trade['type'] not in ['market', 'limit', 'stop', 'take_profit', 'stop_limit']:
            errors.append(f"Invalid order type: {trade['type']}")
        
        if trade['amount'] <= 0:
            errors.append(f"Invalid amount: {trade['amount']}")
        
        if trade['price'] <= 0:
            errors.append(f"Invalid price: {trade['price']}")
        
        if 'fee' in trade and trade['fee'] < 0:
            errors.append(f"Negative fee: {trade['fee']}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_position(self, position: Dict) -> Tuple[bool, List[str]]:
        errors = []
        
        required_fields = ['symbol', 'side', 'size', 'entry_price']
        for field in required_fields:
            if field not in position:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        if position['side'] not in ['long', 'short']:
            errors.append(f"Invalid position side: {position['side']}")
        
        if position['size'] <= 0:
            errors.append(f"Invalid position size: {position['size']}")
        
        if position['entry_price'] <= 0:
            errors.append(f"Invalid entry price: {position['entry_price']}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
