import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class TripleEMAStrategy(BaseStrategy):
    description = """Triple Exponential Moving Average (TEMA) Strategy
    
    This strategy uses three EMAs of different periods:
    - Buy when shortest EMA crosses above medium EMA and both are above longest EMA
    - Sell when shortest EMA crosses below medium EMA and both are below longest EMA
    
    Parameters:
    - Short EMA: {} periods
    - Medium EMA: {} periods
    - Long EMA: {} periods
    """
    
    def __init__(self, initial_capital: float, short_period: int = 5, 
                 medium_period: int = 10, long_period: int = 20):
        super().__init__(initial_capital)
        self.short_period = short_period
        self.medium_period = medium_period
        self.long_period = long_period
        self.description = self.description.format(
            short_period, medium_period, long_period
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate EMAs
        df['EMA_short'] = ta.trend.ema_indicator(df['Close'], self.short_period)
        df['EMA_medium'] = ta.trend.ema_indicator(df['Close'], self.medium_period)
        df['EMA_long'] = ta.trend.ema_indicator(df['Close'], self.long_period)
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy conditions
        buy_condition = (
            (df['EMA_short'] > df['EMA_medium']) & 
            (df['EMA_medium'] > df['EMA_long'])
        )
        
        # Sell conditions
        sell_condition = (
            (df['EMA_short'] < df['EMA_medium']) & 
            (df['EMA_medium'] < df['EMA_long'])
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df 