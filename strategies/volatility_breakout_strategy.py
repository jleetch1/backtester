import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class VolatilityBreakoutStrategy(BaseStrategy):
    description = """Volatility Breakout Strategy
    
    Uses ATR to identify volatility-based breakouts:
    - Buy when price breaks above previous close + ATR multiple
    - Sell when price breaks below previous close - ATR multiple
    
    Parameters:
    - ATR Period: {} days
    - ATR Multiple: {} times ATR
    - Volume Confirmation: {}x average
    """
    
    def __init__(self, initial_capital: float, atr_period: int = 14,
                 atr_multiple: float = 2.0, volume_threshold: float = 1.5):
        super().__init__(initial_capital)
        self.atr_period = atr_period
        self.atr_multiple = atr_multiple
        self.volume_threshold = volume_threshold
        self.description = self.description.format(
            atr_period, atr_multiple, volume_threshold
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate ATR
        atr = ta.volatility.AverageTrueRange(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.atr_period
        )
        df['ATR'] = atr.average_true_range()
        
        # Calculate breakout levels
        df['Upper_Band'] = df['Close'].shift(1) + (df['ATR'] * self.atr_multiple)
        df['Lower_Band'] = df['Close'].shift(1) - (df['ATR'] * self.atr_multiple)
        
        # Calculate volume confirmation
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal: price breaks above upper band with volume confirmation
        buy_condition = (
            (df['High'] > df['Upper_Band']) &
            (df['Volume'] > df['Volume_MA'] * self.volume_threshold)
        )
        
        # Sell signal: price breaks below lower band with volume confirmation
        sell_condition = (
            (df['Low'] < df['Lower_Band']) &
            (df['Volume'] > df['Volume_MA'] * self.volume_threshold)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df