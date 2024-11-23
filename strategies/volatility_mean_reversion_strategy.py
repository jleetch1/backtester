import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class VolatilityMeanReversionStrategy(BaseStrategy):
    description = """Volatility Mean Reversion Strategy
    
    Combines Bollinger Bands with RSI for mean reversion:
    - Buy on oversold conditions with low volatility
    - Sell on overbought conditions with high volatility
    - Uses dynamic volatility thresholds
    
    Parameters:
    - BB Period: {} (Bollinger Band period)
    - BB Std: {} (Standard deviation multiplier)
    - RSI Period: {} (RSI calculation period)
    - Vol Lookback: {} (Volatility lookback period)
    """
    
    def __init__(self, initial_capital: float, bb_period: int = 20,
                 bb_std: float = 2.0, rsi_period: int = 14,
                 vol_lookback: int = 50):
        super().__init__(initial_capital)
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.vol_lookback = vol_lookback
        self.description = self.description.format(
            bb_period, bb_std, rsi_period, vol_lookback
        )
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Bollinger Bands
        bb_indicator = ta.volatility.BollingerBands(
            close=df['Close'],
            window=self.bb_period,
            window_dev=self.bb_std
        )
        df['BB_upper'] = bb_indicator.bollinger_hband()
        df['BB_lower'] = bb_indicator.bollinger_lband()
        df['BB_middle'] = bb_indicator.bollinger_mavg()
        
        # Calculate RSI
        df['RSI'] = ta.momentum.RSIIndicator(
            close=df['Close'],
            window=self.rsi_period
        ).rsi()
        
        # Calculate Historical Volatility
        df['Returns'] = df['Close'].pct_change()
        df['Historical_Vol'] = df['Returns'].rolling(window=self.vol_lookback).std()
        df['Vol_Percentile'] = df['Historical_Vol'].rolling(window=self.vol_lookback).rank(pct=True)
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy conditions: Low volatility, oversold RSI, price near lower band
        buy_condition = (
            (df['Vol_Percentile'] < 0.3) &  # Low volatility regime
            (df['RSI'] < 30) &  # Oversold
            (df['Close'] <= df['BB_lower'])  # Price at or below lower band
        )
        
        # Sell conditions: High volatility, overbought RSI, price near upper band
        sell_condition = (
            (df['Vol_Percentile'] > 0.7) &  # High volatility regime
            (df['RSI'] > 70) &  # Overbought
            (df['Close'] >= df['BB_upper'])  # Price at or above upper band
        )
        
        df.loc[buy_condition, 'Signal'] = 1
        df.loc[sell_condition, 'Signal'] = -1
        
        return df