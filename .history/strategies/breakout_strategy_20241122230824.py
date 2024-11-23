import pandas as pd
from strategies.base_strategy import BaseStrategy

class BreakoutStrategy(BaseStrategy):
    description = """Breakout Strategy
    
    Identifies and trades breakouts from price ranges:
    - Buy when price breaks above recent high with volume confirmation
    - Sell when price breaks below recent low with volume confirmation
    
    Parameters:
    - Lookback Period: {} days
    - Volume Threshold: {}x average
    """
    
    def __init__(self, initial_capital: float, lookback_period: int = 20,
                 volume_threshold: float = 1.5):
        super().__init__(initial_capital)
        self.lookback_period = lookback_period
        self.volume_threshold = volume_threshold
        self.description = self.description.format(
            lookback_period, volume_threshold
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate rolling high, low, and average volume
        df['Rolling_High'] = df['High'].rolling(window=self.lookback_period).max()
        df['Rolling_Low'] = df['Low'].rolling(window=self.lookback_period).min()
        df['Volume_MA'] = df['Volume'].rolling(window=self.lookback_period).mean()
        
        # Calculate price channels
        df['Upper_Channel'] = df['Rolling_High'].shift(1)
        df['Lower_Channel'] = df['Rolling_Low'].shift(1)
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal: breakout above upper channel with volume confirmation
        buy_condition = (
            (df['Close'] > df['Upper_Channel']) &
            (df['Volume'] > df['Volume_MA'] * self.volume_threshold)
        )
        
        # Sell signal: breakdown below lower channel with volume confirmation
        sell_condition = (
            (df['Close'] < df['Lower_Channel']) &
            (df['Volume'] > df['Volume_MA'] * self.volume_threshold)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df 