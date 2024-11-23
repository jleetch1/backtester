import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class MomentumStrategy(BaseStrategy):
    description = """Price Momentum Strategy
    
    Uses price momentum and rate of change to identify trends:
    - Buy when momentum crosses above threshold with increasing volume
    - Sell when momentum crosses below threshold or reverses
    
    Parameters:
    - Momentum Period: {} periods
    - Buy Threshold: {}%
    - Sell Threshold: {}%
    - Volume Factor: {}x
    """
    
    def __init__(self, initial_capital: float, momentum_period: int = 10,
                 buy_threshold: float = 2.0, sell_threshold: float = -1.0,
                 volume_factor: float = 1.5):
        super().__init__(initial_capital)
        self.momentum_period = momentum_period
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        self.volume_factor = volume_factor
        self.description = self.description.format(
            momentum_period, buy_threshold, sell_threshold, volume_factor
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate momentum (rate of change)
        df['Momentum'] = df['Close'].pct_change(periods=self.momentum_period) * 100
        
        # Calculate volume moving average
        df['Volume_MA'] = df['Volume'].rolling(window=self.momentum_period).mean()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy conditions
        buy_condition = (
            (df['Momentum'] > self.buy_threshold) &
            (df['Volume'] > df['Volume_MA'] * self.volume_factor)
        )
        
        # Sell conditions
        sell_condition = (
            (df['Momentum'] < self.sell_threshold) |
            (df['Momentum'] < df['Momentum'].shift(1))  # Momentum reversal
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df