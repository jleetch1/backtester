import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class RSIStrategy(BaseStrategy):
    description = """Relative Strength Index (RSI) Strategy
    
    This strategy uses the RSI indicator to identify overbought and oversold conditions:
    - Buy when RSI falls below the oversold level ({} - oversold)
    - Sell when RSI rises above the overbought level ({} - overbought)
    
    Parameters:
    - RSI Period: {} days
    - Oversold level: {}
    - Overbought level: {}
    """
    
    def __init__(self, initial_capital: float, rsi_period: int = 14,
                 oversold: float = 30, overbought: float = 70):
        super().__init__(initial_capital)
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.description = self.description.format(
            oversold, overbought, rsi_period, oversold, overbought
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], self.rsi_period).rsi()
        
        # Generate signals
        df['Signal'] = 0
        df.loc[df['RSI'] < self.oversold, 'Signal'] = 1  # Buy signal
        df.loc[df['RSI'] > self.overbought, 'Signal'] = -1  # Sell signal
        
        return df 