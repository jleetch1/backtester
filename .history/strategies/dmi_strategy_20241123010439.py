import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta.trend as trend

class DMIStrategy(BaseStrategy):
    description = """Directional Movement Index (DMI) Strategy
    
    Uses DMI and ADX to identify strong trending moves:
    - Buy when +DI crosses above -DI with strong ADX
    - Sell when -DI crosses above +DI with strong ADX
    
    Parameters:
    - DMI Period: {} periods
    - ADX Threshold: {}
    """
    
    def __init__(self, initial_capital: float, dmi_period: int = 14,
                 adx_threshold: float = 25):
        super().__init__(initial_capital)
        self.dmi_period = dmi_period
        self.adx_threshold = adx_threshold
        self.description = self.description.format(
            dmi_period, adx_threshold
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate DMI and ADX using ADXIndicator instead of DMIIndicator
        adx_indicator = trend.ADXIndicator(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.dmi_period
        )
        
        df['DI_plus'] = adx_indicator.adx_pos()
        df['DI_minus'] = adx_indicator.adx_neg()
        df['ADX'] = adx_indicator.adx()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal: +DI crosses above -DI with strong ADX
        buy_condition = (
            (df['DI_plus'] > df['DI_minus']) &
            (df['DI_plus'].shift(1) <= df['DI_minus'].shift(1)) &
            (df['ADX'] > self.adx_threshold)
        )
        
        # Sell signal: -DI crosses above +DI with strong ADX
        sell_condition = (
            (df['DI_minus'] > df['DI_plus']) &
            (df['DI_minus'].shift(1) <= df['DI_plus'].shift(1)) &
            (df['ADX'] > self.adx_threshold)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df