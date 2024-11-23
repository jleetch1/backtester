import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class MACDStrategy(BaseStrategy):
    description = """MACD (Moving Average Convergence Divergence) Strategy
    
    This strategy uses the MACD indicator to generate signals:
    - Buy when MACD line crosses above the signal line
    - Sell when MACD line crosses below the signal line
    
    Parameters:
    - Fast EMA: {} periods
    - Slow EMA: {} periods
    - Signal EMA: {} periods
    """
    
    def __init__(self, initial_capital: float, fast_period: int = 12, 
                 slow_period: int = 26, signal_period: int = 9):
        super().__init__(initial_capital)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.description = self.description.format(
            fast_period, slow_period, signal_period
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate MACD
        macd = ta.trend.MACD(
            close=df['Close'],
            window_slow=self.slow_period,
            window_fast=self.fast_period,
            window_sign=self.signal_period
        )
        
        df['MACD'] = macd.macd()
        df['Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Generate trading signals
        df['Signal'] = 0
        
        # Buy signal: MACD crosses above signal line
        df.loc[df['MACD'] > df['Signal'], 'Signal'] = 1
        
        # Sell signal: MACD crosses below signal line
        df.loc[df['MACD'] < df['Signal'], 'Signal'] = -1
        
        return df 