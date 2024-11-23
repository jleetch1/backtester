from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.position = 0
        self.capital = initial_capital
        self.trades = []
        
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate buy/sell signals for the given data
        Returns DataFrame with additional columns for signals
        """
        pass
    
    def get_position_size(self, price: float) -> float:
        """Calculate position size based on available capital"""
        return self.capital / price 