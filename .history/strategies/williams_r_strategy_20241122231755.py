import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class WilliamsRStrategy(BaseStrategy):
    description = """Williams %R Strategy
    
    Uses Williams %R indicator to identify overbought/oversold conditions:
    - Buy when Williams %R crosses above oversold threshold
    - Sell when Williams %R crosses below overbought threshold
    
    Parameters:
    - Period: {} days
    - Overbought Level: {}
    - Oversold Level: {}
    """
    
    def __init__(self, initial_capital: float, period: int = 14,
                 overbought: float = -20, oversold: float = -80):
        super().__init__(initial_capital)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        self.description = self.description.format(
            period, overbought, oversold
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Williams %R
        indicator_wr = ta.momentum.WilliamsRIndicator(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            lbp=self.period
        )
        
        df['WR'] = indicator_wr.williams_r()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal when crossing above oversold level
        buy_condition = (
            (df['WR'].shift(1) <= self.oversold) &
            (df['WR'] > self.oversold)
        )
        
        # Sell signal when crossing below overbought level
        sell_condition = (
            (df['WR'].shift(1) >= self.overbought) &
            (df['WR'] < self.overbought)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df 