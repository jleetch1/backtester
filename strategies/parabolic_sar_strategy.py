import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class ParabolicSARStrategy(BaseStrategy):
    description = """Parabolic SAR Strategy
    
    Uses the Parabolic Stop and Reverse (SAR) indicator:
    - Buy when price crosses above SAR
    - Sell when price crosses below SAR
    
    Parameters:
    - Step: {} (acceleration factor)
    - Maximum Step: {} (maximum acceleration)
    """
    
    def __init__(self, initial_capital: float, step: float = 0.02, 
                 max_step: float = 0.2):
        super().__init__(initial_capital)
        self.step = step
        self.max_step = max_step
        self.description = self.description.format(step, max_step)
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Parabolic SAR
        indicator_psar = ta.trend.PSARIndicator(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            step=self.step,
            max_step=self.max_step
        )
        
        df['SAR'] = indicator_psar.psar()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal when price crosses above SAR
        df.loc[df['Close'] > df['SAR'], 'Signal'] = 1
        
        # Sell signal when price crosses below SAR
        df.loc[df['Close'] < df['SAR'], 'Signal'] = -1
        
        return df 