import yfinance as yf
import ccxt
import pandas as pd
from datetime import datetime

class DataFetcher:
    STOCK_TIMEFRAMES = {
        '1m': '1m',
        '2m': '2m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '60m': '1h',
        '1d': '1d',
        '1wk': '1wk',
        '1mo': '1mo'
    }
    
    CRYPTO_TIMEFRAMES = {
        '1m': '1m',
        '3m': '3m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '1h',
        '2h': '2h',
        '4h': '4h',
        '6h': '6h',
        '8h': '8h',
        '12h': '12h',
        '1d': '1d',
        '3d': '3d',
        '1w': '1w',
        '1M': '1M'
    }

    def __init__(self):
        self.crypto_exchange = ccxt.binance()
        
    def get_stock_data(self, symbol: str, start_date: datetime, end_date: datetime, interval='1d') -> pd.DataFrame:
        """
        Fetch stock data from Yahoo Finance
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            interval: Data interval ('1m','2m','5m','15m','30m','60m','1d','1wk','1mo')
        """
        ticker = yf.Ticker(symbol)
        df = ticker.history(interval=interval, start=start_date, end=end_date)
        return df
        
    def get_crypto_data(self, symbol: str, start_date: datetime, end_date: datetime, interval='1d') -> pd.DataFrame:
        """
        Fetch crypto data from Binance
        
        Args:
            symbol: Crypto pair (e.g., 'BTC/USDT')
            start_date: Start date
            end_date: End date
            interval: Data interval ('1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M')
        """
        since = int(start_date.timestamp() * 1000)
        limit = None
        
        ohlcv = self.crypto_exchange.fetch_ohlcv(
            symbol, 
            timeframe=interval,
            since=since,
            limit=limit
        )
        
        df = pd.DataFrame(
            ohlcv,
            columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
        )
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df.set_index('Timestamp', inplace=True)
        
        return df[df.index <= end_date]

    @classmethod
    def get_available_timeframes(cls, data_type='stock'):
        """Get available timeframes for the specified data type"""
        if data_type.lower() == 'stock':
            return list(cls.STOCK_TIMEFRAMES.keys())
        elif data_type.lower() == 'crypto':
            return list(cls.CRYPTO_TIMEFRAMES.keys())
        return []