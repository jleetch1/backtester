import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class BollingerBandsStrategy(BaseStrategy):
    description = """Bollinger Bands Strategy
    
    This strategy uses Bollinger Bands to identify overbought/oversold conditions:
    - Buy when price touches or crosses below the lower band
    - Sell when price touches or crosses above the upper band
    
    Parameters:
    - Period: {} days
    - Standard Deviations: {}
    """
    
    def __init__(self, initial_capital: float, period: int = 20, std_dev: float = 2.0):
        super().__init__(initial_capital)
        self.period = period
        self.std_dev = std_dev
        self.description = self.description.format(period, std_dev)
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Bollinger Bands
        indicator_bb = ta.volatility.BollingerBands(
            close=df["Close"], 
            window=self.period, 
            window_dev=self.std_dev
        )
        
        df['BB_upper'] = indicator_bb.bollinger_hband()
        df['BB_middle'] = indicator_bb.bollinger_mavg()
        df['BB_lower'] = indicator_bb.bollinger_lband()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal when price crosses below lower band
        df.loc[df['Close'] <= df['BB_lower'], 'Signal'] = 1
        
        # Sell signal when price crosses above upper band
        df.loc[df['Close'] >= df['BB_upper'], 'Signal'] = -1
        
        return df 