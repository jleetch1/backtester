import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta
import numpy as np

class SupertrendStrategy(BaseStrategy):
    description = """Supertrend Strategy
    
    Uses Supertrend indicator for trend following:
    - Buy when price crosses above Supertrend line
    - Sell when price crosses below Supertrend line
    - Incorporates ATR for volatility-based adjustments
    
    Parameters:
    - ATR Period: {} periods
    - ATR Multiplier: {} (for band calculation)
    - Trend Confirmation: {} periods
    """
    
    def __init__(self, initial_capital: float, atr_period: int = 10,
                 atr_multiplier: float = 3.0, trend_confirmation: int = 3):
        super().__init__(initial_capital)
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.trend_confirmation = trend_confirmation
        self.description = self.description.format(
            atr_period, atr_multiplier, trend_confirmation
        )
    
    def _calculate_supertrend(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Supertrend indicator"""
        # Calculate ATR
        atr = ta.volatility.AverageTrueRange(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.atr_period
        ).average_true_range()
        
        # Calculate basic upper and lower bands
        hl2 = (df['High'] + df['Low']) / 2
        upper_band = hl2 + (self.atr_multiplier * atr)
        lower_band = hl2 - (self.atr_multiplier * atr)
        
        # Initialize Supertrend
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        
        # Calculate Supertrend
        for i in range(self.atr_period, len(df)):
            if df['Close'].iloc[i] > upper_band.iloc[i-1]:
                direction.iloc[i] = 1
            elif df['Close'].iloc[i] < lower_band.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1]
                
            if direction.iloc[i] == 1:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]
        
        return supertrend, direction
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Supertrend
        df['Supertrend'], df['Direction'] = self._calculate_supertrend(df)
        
        # Generate signals
        df['Signal'] = 0
        
        # Trend confirmation using rolling window
        df['Trend_Confirmed'] = df['Direction'].rolling(
            window=self.trend_confirmation
        ).apply(lambda x: 1 if all(i == 1 for i in x) else 
                        -1 if all(i == -1 for i in x) else 0)
        
        # Buy signal: Price crosses above Supertrend with confirmation
        buy_condition = (
            (df['Close'] > df['Supertrend']) &
            (df['Trend_Confirmed'] == 1)
        )
        
        # Sell signal: Price crosses below Supertrend with confirmation
        sell_condition = (
            (df['Close'] < df['Supertrend']) &
            (df['Trend_Confirmed'] == -1)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df