import yfinance as yf
import ccxt
import pandas as pd
from datetime import datetime

class DataFetcher:
    def __init__(self):
        self.crypto_exchange = ccxt.binance()
        
    def get_stock_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch stock data from Yahoo Finance"""
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        return df
        
    def get_crypto_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Fetch crypto data from Binance"""
        timeframe = '1d'
        since = int(start_date.timestamp() * 1000)
        limit = None
        
        ohlcv = self.crypto_exchange.fetch_ohlcv(
            symbol, 
            timeframe=timeframe,
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