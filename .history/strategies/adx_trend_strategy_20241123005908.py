import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta.trend as trend

class ADXTrendStrategy(BaseStrategy):
    description = """ADX Trend Strategy
    
    Uses ADX (Average Directional Index) to identify strong trends:
    - Buy when ADX > threshold and +DI crosses above -DI
    - Sell when ADX > threshold and +DI crosses below -DI
    
    Parameters:
    - ADX Period: {}
    - ADX Threshold: {}
    """
    
    def __init__(self, initial_capital: float, adx_period: int = 14, 
                 adx_threshold: float = 25):
        super().__init__(initial_capital)
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.description = self.description.format(
            adx_period, adx_threshold
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate ADX and directional indicators using DirectionalMovementIndex
        adx_indicator = trend.ADXIndicator(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.adx_period
        )
        
        df['ADX'] = adx_indicator.adx()
        df['DI_pos'] = adx_indicator.adx_pos()
        df['DI_neg'] = adx_indicator.adx_neg()
        
        # Generate signals
        df['Signal'] = 0
        
        # Strong trend conditions
        strong_trend = df['ADX'] > self.adx_threshold
        
        # Buy signal: Strong trend and +DI crosses above -DI
        buy_condition = (
            strong_trend & 
            (df['DI_pos'] > df['DI_neg'])
        )
        
        # Sell signal: Strong trend and +DI crosses below -DI
        sell_condition = (
            strong_trend & 
            (df['DI_pos'] < df['DI_neg'])
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df 