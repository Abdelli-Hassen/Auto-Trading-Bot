import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import config
from utils import setup_logger

class MonitoringSystem:
    def __init__(self):
        self.logger = setup_logger("Monitor", "monitor.log")
        self.alerts_sent = []
        self.metrics_history = []
        
    def log_trade(self, trade: Dict):
        """Log a trade execution."""
        self.logger.info(f"TRADE EXECUTED: {trade}")
        
        # Could send to external monitoring service, database, etc.
        # For now, just log locally
        
    def log_signal(self, signal: Dict, strategy_name: str):
        """Log a trading signal."""
        self.logger.info(f"SIGNAL [{strategy_name}]: {signal}")
        
    def log_error(self, error: str, context: str = ""):
        """Log an error."""
        self.logger.error(f"ERROR [{context}]: {error}")
        
    def log_performance(self, metrics: Dict):
        """Log performance metrics."""
        self.logger.info(f"PERFORMANCE: {json.dumps(metrics, indent=2)}")
        self.metrics_history.append({
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        })
        
    def send_alert(self, message: str, level: str = "INFO"):
        """Send an alert (could be email, Telegram, etc.)."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        
        self.alerts_sent.append(alert)
        
        # Log the alert
        if level == "ERROR":
            self.logger.error(f"ALERT: {message}")
        elif level == "WARNING":
            self.logger.warning(f"ALERT: {message}")
        else:
            self.logger.info(f"ALERT: {message}")
            
        # In a real system, you would send this via Telegram, email, etc.
        # For demo purposes, we'll just log it
        
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent alerts."""
        return self.alerts_sent[-limit:] if self.alerts_sent else []
        
    def get_performance_history(self, limit: int = 100) -> List[Dict]:
        """Get recent performance metrics."""
        return self.metrics_history[-limit:] if self.metrics_history else []
        
    def create_dashboard_data(self) -> Dict:
        """Create data for a dashboard."""
        return {
            'timestamp': datetime.now().isoformat(),
            'alerts_count': len(self.alerts_sent),
            'recent_alerts': self.get_recent_alerts(5),
            'metrics_count': len(self.metrics_history)
        }

# Global monitoring instance
monitor = MonitoringSystem()

def log_trade(trade: Dict):
    monitor.log_trade(trade)

def log_signal(signal: Dict, strategy_name: str):
    monitor.log_signal(signal, strategy_name)

def log_error(error: str, context: str = ""):
    monitor.log_error(error, context)

def log_performance(metrics: Dict):
    monitor.log_performance(metrics)

def send_alert(message: str, level: str = "INFO"):
    monitor.send_alert(message, level)

def get_monitor() -> MonitoringSystem:
    return monitor