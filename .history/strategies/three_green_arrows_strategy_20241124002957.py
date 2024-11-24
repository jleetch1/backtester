import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class ThreeGreenArrowsStrategy(BaseStrategy):
    description = """Three Green Arrows Strategy
    
    Uses three technical indicators to generate buy signals:
    - Moving Average: Price above MA indicates uptrend
    - MACD: Positive MACD histogram indicates momentum
    - Stochastic: Rising above 25 indicates momentum from oversold
    
    Parameters:
    - MA Period: {} days
    - MACD Fast Period: {}
    - MACD Slow Period: {}
    - MACD Signal Period: {}
    - Stochastic Period: {}
    - Stop Loss: {}%
    - Take Profit: {}%
    """
    
    def __init__(self, initial_capital: float, ma_period: int = 30,
                 macd_fast: int = 12, macd_slow: int = 26, macd_signal: int = 9,
                 stoch_period: int = 14, stop_loss: float = 3.0, take_profit: float = 2.0):
        super().__init__(initial_capital)
        self.ma_period = ma_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.stoch_period = stoch_period
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.description = self.description.format(
            ma_period, macd_fast, macd_slow, macd_signal,
            stoch_period, stop_loss, take_profit
        )
        self.entry_price = 0
        self.stop_price = 0
        self.take_profit_price = 0
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Moving Average
        df['MA'] = ta.trend.sma_indicator(df['Close'], window=self.ma_period)
        
        # Calculate MACD
        macd = ta.trend.MACD(
            close=df['Close'],
            window_slow=self.macd_slow,
            window_fast=self.macd_fast,
            window_sign=self.macd_signal
        )
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Calculate Stochastic
        stoch = ta.momentum.StochasticOscillator(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.stoch_period
        )
        df['Stoch'] = stoch.stoch()
        
        # Generate signals
        df['Signal'] = 0
        
        for idx, row in df.iterrows():
            if self.position == 0:
                # Check for buy signal - all three arrows aligned
                buy_signal = (
                    row['Close'] > row['MA'] and  # Price above MA
                    row['MACD_Hist'] > 0 and      # Positive MACD histogram
                    row['Stoch'] > 25             # Stochastic above oversold
                )
                
                if buy_signal:
                    self.position = self.get_position_size(row['Close'])
                    self.entry_price = row['Close']
                    self.stop_price = self.entry_price * (1 - self.stop_loss / 100)
                    self.take_profit_price = self.entry_price * (1 + self.take_profit / 100)
                    df.at[idx, 'Signal'] = 1
            
            else:
                # Check for exit conditions
                exit_signal = (
                    row['Close'] < row['MA'] or       # Price below MA
                    row['MACD_Hist'] < 0 or           # Negative MACD histogram
                    row['Low'] <= self.stop_price or  # Stop loss hit
                    row['High'] >= self.take_profit_price  # Take profit hit
                )
                
                if exit_signal:
                    df.at[idx, 'Signal'] = -1
                    self.position = 0
                    self.entry_price = 0
                    self.stop_price = 0
                    self.take_profit_price = 0
        
        return df