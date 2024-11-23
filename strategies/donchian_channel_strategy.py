import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class DonchianChannelStrategy(BaseStrategy):
    description = """Donchian Channel Strategy
    
    Uses Donchian Channels to identify breakouts:
    - Buy when price breaks above the upper channel
    - Sell when price breaks below the lower channel
    
    Parameters:
    - Channel Period: {} periods
    - Exit Period: {} periods (shorter period for exits)
    """
    
    def __init__(self, initial_capital: float, channel_period: int = 20, 
                 exit_period: int = 10):
        super().__init__(initial_capital)
        self.channel_period = channel_period
        self.exit_period = exit_period
        self.description = self.description.format(
            channel_period, exit_period
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Donchian Channels
        df['Upper_Channel'] = df['High'].rolling(window=self.channel_period).max()
        df['Lower_Channel'] = df['Low'].rolling(window=self.channel_period).min()
        df['Middle_Channel'] = (df['Upper_Channel'] + df['Lower_Channel']) / 2
        
        # Calculate exit channels (shorter period)
        df['Exit_Upper'] = df['High'].rolling(window=self.exit_period).max()
        df['Exit_Lower'] = df['Low'].rolling(window=self.exit_period).min()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal: breakout above upper channel
        buy_condition = df['Close'] > df['Upper_Channel'].shift(1)
        
        # Sell signal: breakdown below lower channel or exit channel
        sell_condition = df['Close'] < df['Exit_Lower'].shift(1)
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df