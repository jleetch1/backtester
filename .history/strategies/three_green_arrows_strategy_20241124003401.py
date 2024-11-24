import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class ThreeGreenArrowsStrategy(BaseStrategy):
    description = """Three Green Arrows Strategy
    
    Combines three technical indicators for buy signals:
    1. Moving Average: Price CLOSES above MA for trend confirmation
    2. MACD Histogram: Crosses above signal line for momentum
    3. Stochastic: Crosses above 25 from oversold
    
    Risk Management:
    - Stop Loss: 3% below 2-week low
    - Max Risk: 2% per trade
    - Max Position: 25% of portfolio
    - No entry if close > 10% above 30-day MA
    """
    
    def __init__(self, initial_capital: float):
        super().__init__(initial_capital)
        self.ma_period = 30  # 30-day moving average
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.stoch_period = 14
        self.description = self.description
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # 1. Moving Average - specifically checking CLOSING price
        df['MA'] = ta.trend.sma_indicator(df['Close'], window=self.ma_period)
        df['Close_Above_MA'] = df['Close'] > df['MA']
        df['MA_Distance'] = ((df['Close'] - df['MA']) / df['MA']) * 100
        
        # 2. MACD
        macd = ta.trend.MACD(
            close=df['Close'],
            window_slow=self.macd_slow,
            window_fast=self.macd_fast,
            window_sign=self.macd_signal
        )
        df['MACD_Hist'] = macd.macd_diff()
        df['MACD_Signal'] = df['MACD_Hist'] > 0
        
        # 3. Stochastic
        stoch = ta.momentum.StochasticOscillator(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.stoch_period
        )
        df['Stoch'] = stoch.stoch()
        df['Stoch_Signal'] = (df['Stoch'] > 25) & (df['Stoch'].shift(1) <= 25)
        
        # Calculate 2-week low for stop loss
        df['Two_Week_Low'] = df['Low'].rolling(window=10).min()
        
        # Generate signals
        df['Signal'] = 0
        
        for idx in range(len(df)):
            if idx < 10:  # Need enough data for calculations
                continue
                
            if self.position == 0:
                # Check all three arrows align
                three_arrows_aligned = (
                    df['Close_Above_MA'].iloc[idx] and     # Arrow 1: Close above MA
                    df['MACD_Signal'].iloc[idx] and        # Arrow 2: MACD positive
                    df['Stoch_Signal'].iloc[idx] and       # Arrow 3: Stoch crosses 25
                    df['MA_Distance'].iloc[idx] <= 10      # Not too extended
                )
                
                if three_arrows_aligned:
                    current_price = df['Close'].iloc[idx]
                    stop_price = df['Two_Week_Low'].iloc[idx] * 0.97  # 3% below 2-week low
                    risk_per_share = current_price - stop_price
                    
                    # Position sizing based on 2% risk
                    max_risk = self.initial_capital * 0.02
                    position_size = min(
                        max_risk / risk_per_share,  # Size based on risk
                        self.initial_capital * 0.25  # Max 25% of portfolio
                    )
                    
                    self.position = position_size
                    self.entry_price = current_price
                    self.stop_price = stop_price
                    df.at[df.index[idx], 'Signal'] = 1
            
            else:
                # Exit conditions
                exit_signal = (
                    not df['Close_Above_MA'].iloc[idx] or  # Close falls below MA
                    df['Low'].iloc[idx] <= self.stop_price  # Stop loss hit
                )
                
                if exit_signal:
                    df.at[df.index[idx], 'Signal'] = -1
                    self.position = 0
                    self.entry_price = 0
                    self.stop_price = 0
        
        return df