import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy

class IchimokuStrategy(BaseStrategy):
    description = """Ichimoku Cloud Strategy
    
    This strategy uses the Ichimoku Cloud indicator for signals:
    - Buy when price crosses above the cloud and Tenkan-sen crosses above Kijun-sen
    - Sell when price crosses below the cloud and Tenkan-sen crosses below Kijun-sen
    
    Parameters:
    - Tenkan-sen Period: {} (Conversion Line)
    - Kijun-sen Period: {} (Base Line)
    - Senkou Span B Period: {} (Leading Span B)
    """
    
    def __init__(self, initial_capital: float, tenkan_period: int = 9, 
                 kijun_period: int = 26, senkou_b_period: int = 52):
        super().__init__(initial_capital)
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.description = self.description.format(
            tenkan_period, kijun_period, senkou_b_period
        )
    
    def _get_ichimoku_lines(self, high, low, period):
        """Calculate ichimoku line for given period"""
        high_values = high.rolling(window=period).max()
        low_values = low.rolling(window=period).min()
        return (high_values + low_values) / 2
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Ichimoku lines
        df['Tenkan'] = self._get_ichimoku_lines(df['High'], df['Low'], self.tenkan_period)
        df['Kijun'] = self._get_ichimoku_lines(df['High'], df['Low'], self.kijun_period)
        
        # Calculate Cloud (Senkou Span A & B)
        df['Senkou_A'] = ((df['Tenkan'] + df['Kijun']) / 2).shift(self.kijun_period)
        df['Senkou_B'] = self._get_ichimoku_lines(df['High'], df['Low'], 
                                                 self.senkou_b_period).shift(self.kijun_period)
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signals
        buy_condition = (
            (df['Close'] > df['Senkou_A']) & 
            (df['Close'] > df['Senkou_B']) & 
            (df['Tenkan'] > df['Kijun'])
        )
        
        # Sell signals
        sell_condition = (
            (df['Close'] < df['Senkou_A']) & 
            (df['Close'] < df['Senkou_B']) & 
            (df['Tenkan'] < df['Kijun'])
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df 