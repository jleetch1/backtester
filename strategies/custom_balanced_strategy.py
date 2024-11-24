import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class CustomBalancedStrategy(BaseStrategy):
    description = """Custom Balanced Strategy
    
    A versatile strategy that adapts to both trending and ranging markets:
    - Identifies trend direction using Moving Averages
    - Confirms momentum with RSI
    - Implements a trailing stop to lock in profits
    - Dynamically adjusts to market conditions
    
    Parameters:
    - Short MA Period: {} days (fast moving average for trend)
    - Long MA Period: {} days (slow moving average for trend)
    - RSI Period: {} days (momentum indicator)
    - RSI Overbought Threshold: {} (momentum sell threshold)
    - RSI Oversold Threshold: {} (momentum buy threshold)
    - Trailing Stop Percentage: {}% (to lock in profits)
    """

    def __init__(self, initial_capital: float, short_ma: int = 50, long_ma: int = 200,
                 rsi_period: int = 14, rsi_overbought: float = 70,
                 rsi_oversold: float = 30, trailing_stop_pct: float = 5.0):
        super().__init__(initial_capital)
        self.short_ma = short_ma
        self.long_ma = long_ma
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.trailing_stop_pct = trailing_stop_pct
        self.entry_price = 0.0
        self.trailing_stop = 0.0
        self.description = self.description.format(
            short_ma, long_ma, rsi_period, rsi_overbought, rsi_oversold, trailing_stop_pct
        )
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Moving Averages for trend identification
        df['MA_short'] = df['Close'].rolling(window=self.short_ma).mean()
        df['MA_long'] = df['Close'].rolling(window=self.long_ma).mean()
        
        # Calculate RSI for momentum
        df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=self.rsi_period).rsi()
        
        # Initialize Signal column
        df['Signal'] = 0
        
        for idx, row in df.iterrows():
            if self.position == 0:
                # Determine trend
                if row['MA_short'] > row['MA_long']:
                    trend = 'uptrend'
                elif row['MA_short'] < row['MA_long']:
                    trend = 'downtrend'
                else:
                    trend = 'neutral'
                
                # Buy Signal: Uptrend and RSI oversold
                if trend == 'uptrend' and row['RSI'] < self.rsi_oversold:
                    self.entry_price = row['Close']
                    self.trailing_stop = self.entry_price * (1 - self.trailing_stop_pct / 100)
                    self.position = self.get_position_size(row['Close'])
                    df.at[idx, 'Signal'] = 1  # Buy signal
                
                # Sell Signal: Downtrend and RSI overbought
                elif trend == 'downtrend' and row['RSI'] > self.rsi_overbought:
                    self.entry_price = row['Close']
                    self.trailing_stop = self.entry_price * (1 + self.trailing_stop_pct / 100)
                    self.position = self.get_position_size(row['Close'])
                    df.at[idx, 'Signal'] = -1  # Sell signal
            
            else:
                if self.position > 0:
                    # Update trailing stop for long position
                    new_trail = row['Close'] * (1 - self.trailing_stop_pct / 100)
                    if new_trail > self.trailing_stop:
                        self.trailing_stop = new_trail
                    
                    # Check if price has fallen below trailing stop
                    if row['Low'] <= self.trailing_stop:
                        df.at[idx, 'Signal'] = -1  # Sell signal to close position
                        self.position = 0
                        self.entry_price = 0.0
                        self.trailing_stop = 0.0
                
                elif self.position < 0:
                    # Update trailing stop for short position
                    new_trail = row['Close'] * (1 + self.trailing_stop_pct / 100)
                    if new_trail < self.trailing_stop:
                        self.trailing_stop = new_trail
                    
                    # Check if price has risen above trailing stop
                    if row['High'] >= self.trailing_stop:
                        df.at[idx, 'Signal'] = 1  # Buy signal to cover position
                        self.position = 0
                        self.entry_price = 0.0
                        self.trailing_stop = 0.0
        
        return df