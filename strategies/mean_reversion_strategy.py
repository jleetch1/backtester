import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy

class MeanReversionStrategy(BaseStrategy):
    description = """Mean Reversion Strategy
    
    Uses standard deviations from moving average to identify extremes:
    - Buy when price is below mean by specified standard deviations
    - Sell when price returns to mean or exceeds opposite threshold
    
    Parameters:
    - MA Period: {}
    - Standard Deviation Threshold: {}
    - Exit Threshold: {}
    """
    
    def __init__(self, initial_capital: float, ma_period: int = 20,
                 std_dev_threshold: float = 2.0, exit_threshold: float = 0.5):
        super().__init__(initial_capital)
        self.ma_period = ma_period
        self.std_dev_threshold = std_dev_threshold
        self.exit_threshold = exit_threshold
        self.description = self.description.format(
            ma_period, std_dev_threshold, exit_threshold
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate moving average and standard deviation
        df['MA'] = df['Close'].rolling(window=self.ma_period).mean()
        df['STD'] = df['Close'].rolling(window=self.ma_period).std()
        
        # Calculate z-score (number of standard deviations from mean)
        df['Z_Score'] = (df['Close'] - df['MA']) / df['STD']
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal: price is below mean by threshold std devs
        buy_condition = df['Z_Score'] <= -self.std_dev_threshold
        
        # Sell signal: price crosses above mean or exceeds opposite threshold
        sell_condition = (
            (df['Z_Score'] >= self.exit_threshold) |
            (df['Z_Score'] >= self.std_dev_threshold)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df 