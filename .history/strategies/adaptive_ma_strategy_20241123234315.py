import pandas as pd
from strategies.base_strategy import BaseStrategy
import numpy as np

class AdaptiveMAStrategy(BaseStrategy):
    description = """Adaptive Moving Average Strategy
    
    Uses Kaufman's Adaptive Moving Average (KAMA):
    - Adapts to market volatility
    - Buy when KAMA turns upward with momentum
    - Sell when KAMA turns downward with momentum
    
    Parameters:
    - Fast Period: {} (fastest EMA)
    - Slow Period: {} (slowest EMA)
    - Efficiency Period: {} (for trend efficiency)
    - Signal Threshold: {} (minimum rate of change)
    """
    
    def __init__(self, initial_capital: float, fast_period: int = 2,
                 slow_period: int = 30, efficiency_period: int = 10,
                 signal_threshold: float = 0.1):
        super().__init__(initial_capital)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.efficiency_period = efficiency_period
        self.signal_threshold = signal_threshold
        self.description = self.description.format(
            fast_period, slow_period, efficiency_period, signal_threshold
        )
    
    def _calculate_kama(self, close: pd.Series) -> pd.Series:
        """Calculate Kaufman's Adaptive Moving Average"""
        try:
            change = abs(close - close.shift(self.efficiency_period))
            volatility = abs(close - close.shift(1)).rolling(self.efficiency_period).sum()
            
            # Handle zero volatility
            er = pd.Series(0, index=close.index)
            mask = volatility != 0
            er[mask] = change[mask] / volatility[mask]
            
            # Calculate smoothing constant
            fast_sc = 2 / (self.fast_period + 1)
            slow_sc = 2 / (self.slow_period + 1)
            sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
            
            # Calculate KAMA
            kama = pd.Series(index=close.index, dtype=float)
            kama.iloc[0] = close.iloc[0]
            
            for i in range(1, len(close)):
                kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (close.iloc[i] - kama.iloc[i-1])
                
            return kama
            
        except Exception as e:
            print(f"Error in KAMA calculation: {str(e)}")
            print(f"Error occurred at line: {e.__traceback__.tb_lineno}")
            raise
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        try:
            df = data.copy()
            print(f"Starting signal generation with {len(df)} rows of data")
            
            # Initialize Signal column first
            df['Signal'] = 0
            
            # Calculate KAMA
            df['KAMA'] = self._calculate_kama(df['Close'])
            print(f"KAMA calculation complete. NaN values: {df['KAMA'].isna().sum()}")
            
            # Calculate KAMA momentum
            df['KAMA_ROC'] = df['KAMA'].pct_change(fill_method=None) * 100
            print(f"ROC calculation complete. NaN values: {df['KAMA_ROC'].isna().sum()}")
            
            # Buy signal: KAMA turning upward with momentum
            buy_condition = (
                (df['KAMA_ROC'] > self.signal_threshold) &
                (df['Close'] > df['KAMA'])
            )
            
            # Sell signal: KAMA turning downward with momentum
            sell_condition = (
                (df['KAMA_ROC'] < -self.signal_threshold) &
                (df['Close'] < df['KAMA'])
            )
            
            df.loc[buy_condition, 'Signal'] = 1
            df.loc[sell_condition, 'Signal'] = -1
            
            print(f"Signal generation complete. Signals generated: {len(df[df['Signal'] != 0])}")
            return df
            
        except Exception as e:
            print(f"Error in AdaptiveMAStrategy signal generation: {str(e)}")
            print(f"Error occurred at line: {e.__traceback__.tb_lineno}")
            raise