import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class CCIStrategy(BaseStrategy):
    description = """Commodity Channel Index (CCI) Strategy
    
    Uses CCI to identify overbought/oversold conditions and trend reversals:
    - Buy when CCI crosses above oversold level
    - Sell when CCI crosses below overbought level
    
    Parameters:
    - CCI Period: {}
    - Overbought Level: {}
    - Oversold Level: {}
    """
    
    def __init__(self, initial_capital: float, cci_period: int = 20,
                 overbought: float = 100, oversold: float = -100):
        super().__init__(initial_capital)
        self.cci_period = cci_period
        self.overbought = overbought
        self.oversold = oversold
        self.description = self.description.format(
            cci_period, overbought, oversold
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate CCI
        cci = ta.trend.CCIIndicator(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.cci_period
        )
        df['CCI'] = cci.cci()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal: CCI crosses above oversold level
        buy_condition = (
            (df['CCI'].shift(1) <= self.oversold) &
            (df['CCI'] > self.oversold)
        )
        
        # Sell signal: CCI crosses below overbought level
        sell_condition = (
            (df['CCI'].shift(1) >= self.overbought) &
            (df['CCI'] < self.overbought)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df 