import pandas as pd
from strategies.base_strategy import BaseStrategy

class PivotPointsStrategy(BaseStrategy):
    description = """Pivot Points Strategy
    
    Uses classic pivot points for support and resistance:
    - Buy when price bounces from support levels
    - Sell when price reverses from resistance levels
    
    Parameters:
    - Pivot Type: {} (Classic/Fibonacci/Camarilla)
    - Bounce Threshold: {}%
    - Confirmation Period: {} bars
    """
    
    def __init__(self, initial_capital: float, pivot_type: str = "Classic",
                 bounce_threshold: float = 0.5, confirmation_period: int = 3):
        super().__init__(initial_capital)
        self.pivot_type = pivot_type
        self.bounce_threshold = bounce_threshold
        self.confirmation_period = confirmation_period
        self.description = self.description.format(
            pivot_type, bounce_threshold, confirmation_period
        )
    
    def _calculate_pivot_points(self, high, low, close):
        """Calculate pivot points and support/resistance levels"""
        pivot = (high + low + close) / 3
        
        if self.pivot_type == "Classic":
            r1 = (2 * pivot) - low
            s1 = (2 * pivot) - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            
        elif self.pivot_type == "Fibonacci":
            r1 = pivot + 0.382 * (high - low)
            s1 = pivot - 0.382 * (high - low)
            r2 = pivot + 0.618 * (high - low)
            s2 = pivot - 0.618 * (high - low)
            
        else:  # Camarilla
            r1 = close + 1.1 * (high - low)
            s1 = close - 1.1 * (high - low)
            r2 = close + 1.2 * (high - low)
            s2 = close - 1