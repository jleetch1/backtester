import pandas as pd
from .base_strategy import BaseStrategy

class MovingAverageCross(BaseStrategy):
    def __init__(self, initial_capital: float, short_window: int = 20, long_window: int = 50):
        super().__init__(initial_capital)
        self.short_window = short_window
        self.long_window = long_window
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate moving averages
        df['SMA_short'] = df['Close'].rolling(window=self.short_window).mean()
        df['SMA_long'] = df['Close'].rolling(window=self.long_window).mean()
        
        # Generate signals
        df['Signal'] = 0
        df.loc[df['SMA_short'] > df['SMA_long'], 'Signal'] = 1  # Buy signal
        df.loc[df['SMA_short'] < df['SMA_long'], 'Signal'] = -1  # Sell signal
        
        return df 