import pandas as pd
from strategies.base_strategy import BaseStrategy

class PivotPointsStrategy(BaseStrategy):
    description = """Pivot Points Strategy
    
    Uses pivot points for support and resistance levels:
    - Buy when price bounces up from support
    - Sell when price bounces down from resistance
    
    Parameters:
    - Pivot Period: {} (daily/weekly)
    - Bounce Threshold: {}%
    """
    
    def __init__(self, initial_capital: float, pivot_period: str = 'daily',
                 bounce_threshold: float = 0.5):
        super().__init__(initial_capital)
        self.pivot_period = pivot_period
        self.bounce_threshold = bounce_threshold
        self.description = self.description.format(
            pivot_period, bounce_threshold
        )
    
    def _calculate_pivot_points(self, df: pd.DataFrame) -> tuple:
        """Calculate pivot points and support/resistance levels"""
        pivot = (df['High'].shift(1) + df['Low'].shift(1) + df['Close'].shift(1)) / 3
        support1 = 2 * pivot - df['High'].shift(1)
        support2 = pivot - (df['High'].shift(1) - df['Low'].shift(1))
        resistance1 = 2 * pivot - df['Low'].shift(1)
        resistance2 = pivot + (df['High'].shift(1) - df['Low'].shift(1))
        
        return pivot, support1, support2, resistance1, resistance2
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate pivot points
        pivot, s1, s2, r1, r2 = self._calculate_pivot_points(df)
        
        df['Signal'] = 0
        
        # Buy signals - price bouncing up from support
        buy_condition = (
            ((df['Low'] <= s1) & (df['Close'] > s1 * (1 + self.bounce_threshold/100))) |
            ((df['Low'] <= s2) & (df['Close'] > s2 * (1 + self.bounce_threshold/100)))
        )
        
        # Sell signals - price bouncing down from resistance
        sell_condition = (
            ((df['High'] >= r1) & (df['Close'] < r1 * (1 - self.bounce_threshold/100))) |
            ((df['High'] >= r2) & (df['Close'] < r2 * (1 - self.bounce_threshold/100)))
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df