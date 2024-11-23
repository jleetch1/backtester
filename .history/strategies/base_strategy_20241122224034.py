from abc import ABC, abstractmethod
import pandas as pd
from enum import Enum

class PositionSizingMethod(Enum):
    CONTRACT_SIZE = "Contract Size"
    EQUITY_PERCENT = "% of Equity"
    SHARES = "# of Shares"
    DOLLAR_AMOUNT = "Dollar Amount"

class BaseStrategy(ABC):
    description = "Base strategy class - not for direct use"
    
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.position = 0
        self.capital = initial_capital
        self.trades = []
        
        # Position sizing defaults
        self.position_sizing_method = PositionSizingMethod.EQUITY_PERCENT
        self.position_size_value = 100  # Default to 100% of equity
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals for the given data
        Returns DataFrame with additional columns for signals
        """
        pass
    
    def get_position_size(self, price: float) -> float:
        """Calculate position size based on selected method and available capital"""
        if self.position_sizing_method == PositionSizingMethod.CONTRACT_SIZE:
            return self.position_size_value
            
        elif self.position_sizing_method == PositionSizingMethod.EQUITY_PERCENT:
            return (self.capital * self.position_size_value / 100) / price
            
        elif self.position_sizing_method == PositionSizingMethod.SHARES:
            return self.position_size_value
            
        elif self.position_sizing_method == PositionSizingMethod.DOLLAR_AMOUNT:
            return self.position_size_value / price
            
        return 0