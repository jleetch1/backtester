import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class StochRSIStrategy(BaseStrategy):
    description = """Stochastic RSI Combined Strategy
    
    This strategy combines Stochastic Oscillator and RSI:
    - Buy when both Stochastic and RSI are oversold
    - Sell when both Stochastic and RSI are overbought
    
    Parameters:
    - Stochastic Period: {}
    - RSI Period: {}
    - Stochastic Overbought: {}
    - Stochastic Oversold: {}
    - RSI Overbought: {}
    - RSI Oversold: {}
    """
    
    def __init__(self, initial_capital: float, stoch_period: int = 14, 
                 rsi_period: int = 14, stoch_overbought: float = 80,
                 stoch_oversold: float = 20, rsi_overbought: float = 70,
                 rsi_oversold: float = 30):
        super().__init__(initial_capital)
        self.stoch_period = stoch_period
        self.rsi_period = rsi_period
        self.stoch_overbought = stoch_overbought
        self.stoch_oversold = stoch_oversold
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.description = self.description.format(
            stoch_period, rsi_period, stoch_overbought,
            stoch_oversold, rsi_overbought, rsi_oversold
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], 
                                           window=self.rsi_period).rsi()
        
        # Calculate Stochastic
        stoch = ta.momentum.StochasticOscillator(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.stoch_period
        )
        df['Stoch_K'] = stoch.stoch()
        df['Stoch_D'] = stoch.stoch_signal()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy when both are oversold
        buy_condition = (
            (df['RSI'] < self.rsi_oversold) & 
            (df['Stoch_K'] < self.stoch_oversold)
        )
        
        # Sell when both are overbought
        sell_condition = (
            (df['RSI'] > self.rsi_overbought) & 
            (df['Stoch_K'] > self.stoch_overbought)
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df 