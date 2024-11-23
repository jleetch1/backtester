import pandas as pd
import numpy as np
from strategies.base_strategy import BaseStrategy

class FibonacciStrategy(BaseStrategy):
    description = """Fibonacci Retracement Strategy
    
    Uses Fibonacci retracement levels to identify potential support/resistance:
    - Identifies swing high/low points
    - Calculates Fibonacci levels (23.6%, 38.2%, 50%, 61.8%)
    - Generates signals based on price interaction with these levels
    
    Parameters:
    - Swing Period: {} (periods to identify swing points)
    - Rebound Threshold: {}% (minimum price move for rebound)
    """
    
    def __init__(self, initial_capital: float, swing_period: int = 20, 
                 rebound_threshold: float = 1.0):
        super().__init__(initial_capital)
        self.swing_period = swing_period
        self.rebound_threshold = rebound_threshold
        self.description = self.description.format(
            swing_period, rebound_threshold
        )
        
    def _find_swing_points(self, data: pd.DataFrame) -> tuple:
        """Identify swing high and low points"""
        highs = []
        lows = []
        
        for i in range(self.swing_period, len(data) - self.swing_period):
            if all(data['High'].iloc[i] > data['High'].iloc[i-j] for j in range(1, self.swing_period+1)) and \
               all(data['High'].iloc[i] > data['High'].iloc[i+j] for j in range(1, self.swing_period+1)):
                highs.append((i, data['High'].iloc[i]))
                
            if all(data['Low'].iloc[i] < data['Low'].iloc[i-j] for j in range(1, self.swing_period+1)) and \
               all(data['Low'].iloc[i] < data['Low'].iloc[i+j] for j in range(1, self.swing_period+1)):
                lows.append((i, data['Low'].iloc[i]))
        
        return highs, lows
    
    def _calculate_fib_levels(self, high: float, low: float) -> dict:
        """Calculate Fibonacci retracement levels"""
        diff = high - low
        return {
            0.236: high - 0.236 * diff,
            0.382: high - 0.382 * diff,
            0.500: high - 0.500 * diff,
            0.618: high - 0.618 * diff
        }
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['Signal'] = 0
        
        # Find swing points
        highs, lows = self._find_swing_points(df)
        
        if not highs or not lows:
            return df
        
        # Process each swing high/low pair
        for i in range(len(df)):
            if i < max(self.swing_period, 1):
                continue
                
            # Find the most recent swing high and low before current point
            recent_high = None
            recent_low = None
            
            for idx, high in reversed(highs):
                if idx < i:
                    recent_high = high
                    break
                    
            for idx, low in reversed(lows):
                if idx < i:
                    recent_low = low
                    break
            
            if recent_high is None or recent_low is None:
                continue
            
            # Calculate Fibonacci levels
            fib_levels = self._calculate_fib_levels(recent_high, recent_low)
            current_price = df['Close'].iloc[i]
            prev_price = df['Close'].iloc[i-1]
            
            # Generate signals based on price interaction with Fibonacci levels
            for level, price_level in fib_levels.items():
                # Buy signal: price bounces up from a Fibonacci level
                if prev_price <= price_level and current_price > price_level and \
                   (current_price - prev_price) / prev_price * 100 >= self.rebound_threshold:
                    df.loc[df.index[i], 'Signal'] = 1
                    break
                    
                # Sell signal: price bounces down from a Fibonacci level
                elif prev_price >= price_level and current_price < price_level and \
                     (prev_price - current_price) / prev_price * 100 >= self.rebound_threshold:
                    df.loc[df.index[i], 'Signal'] = -1
                    break
        
        return df 