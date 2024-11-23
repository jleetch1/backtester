import pandas as pd
from strategies.base_strategy import BaseStrategy
import numpy as np

class VolumePriceTrendStrategy(BaseStrategy):
    description = """Volume Price Trend (VPT) Strategy
    
    Uses volume and price changes to identify trends:
    - Calculates VPT indicator
    - Uses VPT moving averages for signal generation
    - Incorporates volume confirmation
    
    Parameters:
    - Fast MA Period: {}
    - Slow MA Period: {}
    - Volume Threshold: {}x (multiple of average volume)
    """
    
    def __init__(self, initial_capital: float, fast_period: int = 13,
                 slow_period: int = 21, volume_threshold: float = 1.5):
        super().__init__(initial_capital)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.volume_threshold = volume_threshold
        self.description = self.description.format(
            fast_period, slow_period, volume_threshold
        )
    
    def _calculate_vpt(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Price Trend indicator"""
        price_change = df['Close'].pct_change()
        vpt = (price_change * df['Volume']).cumsum()
        return vpt
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate VPT
        df['VPT'] = self._calculate_vpt(df)
        
        # Calculate VPT moving averages
        df['VPT_Fast'] = df['VPT'].rolling(window=self.fast_period).mean()
        df['VPT_Slow'] = df['VPT'].rolling(window=self.slow_period).mean()
        
        # Calculate average volume
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy conditions
        buy_condition = (
            (df['VPT_Fast'] > df['VPT_Slow']) &  # VPT bullish crossover
            (df['Volume'] > df['Volume_MA'] * self.volume_threshold)  # High volume confirmation
        )
        
        # Sell conditions
        sell_condition = (
            (df['VPT_Fast'] < df['VPT_Slow']) &  # VPT bearish crossover
            (df['Volume'] > df['Volume_MA'] * self.volume_threshold)  # High volume confirmation
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df 