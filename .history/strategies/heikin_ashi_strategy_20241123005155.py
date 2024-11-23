import pandas as pd
from strategies.base_strategy import BaseStrategy
import numpy as np

class HeikinAshiStrategy(BaseStrategy):
    description = """Heikin-Ashi Candlestick Strategy
    
    Uses Heikin-Ashi candlesticks to identify trends:
    - Buy when candles turn bullish (hollow) with increasing size
    - Sell when candles turn bearish (filled) with increasing size
    
    Parameters:
    - Trend Length: {} consecutive candles
    - Size Threshold: {}% minimum candle size
    """
    
    def __init__(self, initial_capital: float, trend_length: int = 3,
                 size_threshold: float = 0.5):
        super().__init__(initial_capital)
        self.trend_length = trend_length
        self.size_threshold = size_threshold
        self.description = self.description.format(
            trend_length, size_threshold
        )
        
    def _calculate_heikin_ashi(self, df: pd.DataFrame) -> pd.DataFrame:
        ha = pd.DataFrame(index=df.index)
        
        ha['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
        ha['HA_Open'] = (df['Open'].shift(1) + df['Close'].shift(1)) / 2
        ha.iloc[0, ha.columns.get_loc('HA_Open')] = df['Open'].iloc[0]
        
        ha['HA_High'] = df[['High', 'Open', 'Close']].max(axis=1)
        ha['HA_Low'] = df[['Low', 'Open', 'Close']].min(axis=1)
        
        return ha
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        ha = self._calculate_heikin_ashi(df)
        
        # Calculate candle properties
        ha['Bullish'] = ha['HA_Close'] > ha['HA_Open']
        ha['Size'] = abs(ha['HA_Close'] - ha['HA_Open']) / ha['HA_Open'] * 100
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy condition: consecutive bullish candles with increasing size
        buy_condition = (
            ha['Bullish'].rolling(window=self.trend_length).sum() == self.trend_length &
            (ha['Size'] > self.size_threshold)
        )
        
        # Sell condition: consecutive bearish candles with increasing size
        sell_condition = (
            ha['Bullish'].rolling(window=self.trend_length).sum() == 0 &
            (ha['Size'] > self.size_threshold)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df