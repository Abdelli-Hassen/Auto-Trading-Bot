import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional
import config
from utils import setup_logger

logger = setup_logger("DataStorage", "storage.log")

class DataStorage:
    def __init__(self, db_path: Path = config.DATA_DIR / "storage" / "trading_data.db"):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(str(self.db_path))
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ohlcv (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                symbol TEXT,
                timeframe TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                UNIQUE(timestamp, symbol, timeframe)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                symbol TEXT,
                side TEXT,
                type TEXT,
                amount REAL,
                price REAL,
                cost REAL,
                fee REAL,
                status TEXT,
                order_id TEXT,
                info TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                symbol TEXT,
                side TEXT,
                size REAL,
                entry_price REAL,
                mark_price REAL,
                unrealized_pnl REAL,
                leverage INTEGER,
                UNIQUE(timestamp, symbol)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                equity REAL,
                balance REAL,
                UNIQUE(timestamp)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def store_ohlcv(self, df: pd.DataFrame):
        if df.empty:
            return
        
        conn = self.get_connection()
        df_to_store = df.copy()
        df_to_store['timestamp'] = df_to_store['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        df_to_store.to_sql('ohlcv', conn, if_exists='append', index=False, 
                          dtype={'timestamp': 'TIMESTAMP', 'symbol': 'TEXT', 
                                 'timeframe': 'TEXT', 'open': 'REAL', 'high': 'REAL',
                                 'low': 'REAL', 'close': 'REAL', 'volume': 'REAL'})
        
        conn.commit()
        conn.close()
        logger.debug(f"Stored {len(df)} OHLCV records")
    
    def store_trade(self, trade: dict):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades (timestamp, symbol, side, type, amount, price, cost, fee, status, order_id, info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade.get('timestamp'),
            trade.get('symbol'),
            trade.get('side'),
            trade.get('type'),
            trade.get('amount'),
            trade.get('price'),
            trade.get('cost'),
            trade.get('fee'),
            trade.get('status'),
            trade.get('order_id'),
            str(trade.get('info', {}))
        ))
        
        conn.commit()
        conn.close()
        logger.debug(f"Stored trade: {trade.get('symbol')} {trade.get('side')} {trade.get('amount')}")
    
    def store_position(self, position: dict):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO positions (timestamp, symbol, side, size, entry_price, mark_price, unrealized_pnl, leverage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            position.get('timestamp'),
            position.get('symbol'),
            position.get('side'),
            position.get('size'),
            position.get('entry_price'),
            position.get('mark_price'),
            position.get('unrealized_pnl'),
            position.get('leverage')
        ))
        
        conn.commit()
        conn.close()
        logger.debug(f"Stored position: {position.get('symbol')} {position.get('side')}")
    
    def store_equity(self, equity: float, balance: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO equity (timestamp, equity, balance)
            VALUES (datetime('now'), ?, ?)
        ''', (equity, balance))
        
        conn.commit()
        conn.close()
        logger.debug(f"Stored equity: {equity}")
    
    def get_ohlcv(self, symbol: str, timeframe: str = config.TIMEFRAME, 
                  start_date: str = None, end_date: str = None, limit: int = None) -> pd.DataFrame:
        conn = self.get_connection()
        
        query = '''
            SELECT timestamp, symbol, timeframe, open, high, low, close, volume
            FROM ohlcv
            WHERE symbol = ? AND timeframe = ?
        '''
        params = [symbol, timeframe]
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
        
        query += ' ORDER BY timestamp DESC'
        if limit:
            query += f' LIMIT {limit}'
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        return df
    
    def get_latest_price(self, symbol: str) -> float:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT close FROM ohlcv
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (symbol,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0.0
    
    def get_portfolio_value(self) -> float:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT equity FROM equity
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else config.INITIAL_CAPITAL
    
    def clear_old_data(self, days: int = 30):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM ohlcv
            WHERE timestamp < datetime('now', ?)
        ''', (f'-{days} days',))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Cleared {deleted} old records")
    
    def get_stats(self) -> dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM ohlcv')
        stats['ohlcv_records'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM trades')
        stats['trade_count'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM positions')
        stats['position_count'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM equity')
        stats['equity_records'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
