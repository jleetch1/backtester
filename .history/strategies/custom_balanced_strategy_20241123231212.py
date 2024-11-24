import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta
import numpy as np

class CustomBalancedStrategy(BaseStrategy):
    description = """Enhanced Custom Balanced Strategy
    
    A robust strategy combining multiple technical indicators and advanced risk management:
    - Uses Moving Averages and RSI for trend identification
    - Confirms signals with Stochastic, MFI, and Volume analysis
    - Implements ATR-based dynamic position sizing and stops
    - Features scaled exits and maximum hold time limits
    
    Parameters:
    - Short MA Period: {} days (fast moving average)
    - Long MA Period: {} days (slow moving average)
    - RSI Period: {} days (momentum)
    - Stoch Period: {} days (secondary momentum)
    - ATR Period: {} days (volatility)
    - RSI Overbought: {} (sell threshold)
    - RSI Oversold: {} (buy threshold)
    - ATR Multiplier: {} (for stops)
    - Volume Threshold: {}x (volume confirmation)
    - Max Hold Days: {} (maximum position duration)
    """
    
    def __init__(self, initial_capital: float, short_ma: int = 10, long_ma: int = 30,
                 rsi_period: int = 14, stoch_period: int = 14, atr_period: int = 14,
                 rsi_overbought: float = 70, rsi_oversold: float = 30,
                 atr_multiplier: float = 1.5, volume_threshold: float = 2.0,
                 max_hold_days: int = 20):
        super().__init__(initial_capital)
        self.short_ma = short_ma
        self.long_ma = long_ma
        self.rsi_period = rsi_period
        self.stoch_period = stoch_period
        self.atr_period = atr_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.atr_multiplier = atr_multiplier
        self.volume_threshold = volume_threshold
        self.max_hold_days = max_hold_days
        
        # Trading state variables
        self.entry_price = 0.0
        self.entry_date = None
        self.stop_loss = 0.0
        self.take_profit_1 = 0.0  # First target (50% position)
        self.take_profit_2 = 0.0  # Second target (remaining position)
        self.trailing_stop = 0.0
        self.position_scale = 1.0  # For tracking partial exits
        
        self.description = self.description.format(
            short_ma, long_ma, rsi_period, stoch_period, atr_period,
            rsi_overbought, rsi_oversold, atr_multiplier, volume_threshold,
            max_hold_days
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate core indicators
        df['MA_short'] = df['Close'].rolling(window=self.short_ma).mean()
        df['MA_long'] = df['Close'].rolling(window=self.long_ma).mean()
        df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=self.rsi_period).rsi()
        
        # Calculate Stochastic
        stoch = ta.momentum.StochasticOscillator(
            high=df['High'], low=df['Low'], close=df['Close'],
            window=self.stoch_period
        )
        df['Stoch_K'] = stoch.stoch()
        df['Stoch_D'] = stoch.stoch_signal()
        
        # Calculate MFI for volume-price confirmation
        df['MFI'] = ta.volume.MFIIndicator(
            high=df['High'], low=df['Low'],
            close=df['Close'], volume=df['Volume'],
            window=self.rsi_period
        ).money_flow_index()
        
        # Calculate ATR and Volume metrics
        df['ATR'] = ta.volatility.AverageTrueRange(
            high=df['High'], low=df['Low'], close=df['Close'],
            window=self.atr_period
        ).average_true_range()
        
        df['Volume_MA'] = df['Volume'].rolling(window=self.short_ma).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
        
        # Initialize signals
        df['Signal'] = 0
        df['Position_Size'] = 0.0
        
        for idx, row in df.iterrows():
            if self.position == 0:
                # Determine trend strength
                trend_strength = abs(row['MA_short'] - row['MA_long']) / row['ATR']
                
                # Enhanced buy conditions
                buy_condition = (
                    (row['MA_short'] > row['MA_long']) and          # Uptrend
                    (row['RSI'] < self.rsi_oversold) and           # RSI oversold
                    (row['Stoch_K'] < 20) and                      # Stochastic confirms
                    (row['MFI'] < 30) and                          # MFI confirms
                    (row['Volume_Ratio'] > self.volume_threshold) and  # Volume confirms
                    (trend_strength > 1.5)                         # Strong trend
                )
                
                # Enhanced sell conditions
                sell_condition = (
                    (row['MA_short'] < row['MA_long']) and          # Downtrend
                    (row['RSI'] > self.rsi_overbought) and         # RSI overbought
                    (row['Stoch_K'] > 80) and                      # Stochastic confirms
                    (row['MFI'] > 70) and                          # MFI confirms
                    (row['Volume_Ratio'] > self.volume_threshold) and  # Volume confirms
                    (trend_strength > 1.5)                         # Strong trend
                )
                
                if buy_condition:
                    # Calculate position size (1% risk per trade)
                    risk_per_share = row['ATR'] * self.atr_multiplier
                    position_size = min(
                        self.get_position_size(row['Close']),
                        (self.capital * 0.01) / risk_per_share
                    )
                    
                    self.position = position_size
                    self.entry_price = row['Close']
                    self.entry_date = idx
                    self.stop_loss = self.entry_price - (risk_per_share * 1.5)
                    self.take_profit_1 = self.entry_price + (risk_per_share * 1.5)
                    self.take_profit_2 = self.entry_price + (risk_per_share * 2.5)
                    self.trailing_stop = self.stop_loss
                    
                    df.at[idx, 'Signal'] = 1
                    df.at[idx, 'Position_Size'] = position_size
                
                elif sell_condition:
                    # Similar setup for short positions
                    risk_per_share = row['ATR'] * self.atr_multiplier
                    position_size = min(
                        self.get_position_size(row['Close']),
                        (self.capital * 0.01) / risk_per_share
                    )
                    
                    self.position = -position_size
                    self.entry_price = row['Close']
                    self.entry_date = idx
                    self.stop_loss = self.entry_price + (risk_per_share * 1.5)
                    self.take_profit_1 = self.entry_price - (risk_per_share * 1.5)
                    self.take_profit_2 = self.entry_price - (risk_per_share * 2.5)
                    self.trailing_stop = self.stop_loss
                    
                    df.at[idx, 'Signal'] = -1
                    df.at[idx, 'Position_Size'] = -position_size
            
            else:
                # Check maximum hold time
                days_held = (idx - self.entry_date).days
                if days_held >= self.max_hold_days:
                    df.at[idx, 'Signal'] = -np.sign(self.position)  # Exit signal
                    self._reset_trade_vars()
                    continue
                
                if self.position > 0:  # Long position management
                    # Update trailing stop
                    new_stop = row['Close'] - (row['ATR'] * self.atr_multiplier)
                    if new_stop > self.trailing_stop:
                        self.trailing_stop = new_stop
                    
                    # Scaled exit conditions
                    if self.position_scale == 1.0 and row['High'] >= self.take_profit_1:
                        # Exit half position at first target
                        self.position *= 0.5
                        self.position_scale = 0.5
                        df.at[idx, 'Signal'] = -0.5
                    
                    # Full exit conditions
                    exit_long = (
                        (row['Low'] <= self.trailing_stop) or          # Stop hit
                        (row['High'] >= self.take_profit_2) or         # Final target hit
                        (row['RSI'] > 80 and row['Stoch_K'] > 90)     # Extreme overbought
                    )
                    
                    if exit_long:
                        df.at[idx, 'Signal'] = -self.position_scale
                        self._reset_trade_vars()
                
                elif self.position < 0:  # Short position management
                    # Update trailing stop
                    new_stop = row['Close'] + (row['ATR'] * self.atr_multiplier)
                    if new_stop < self.trailing_stop:
                        self.trailing_stop = new_stop
                    
                    # Scaled exit conditions
                    if self.position_scale == 1.0 and row['Low'] <= self.take_profit_1:
                        # Exit half position at first target
                        self.position *= 0.5
                        self.position_scale = 0.5
                        df.at[idx, 'Signal'] = 0.5
                    
                    # Full exit conditions
                    exit_short = (
                        (row['High'] >= self.trailing_stop) or        # Stop hit
                        (row['Low'] <= self.take_profit_2) or         # Final target hit
                        (row['RSI'] < 20 and row['Stoch_K'] < 10)    # Extreme oversold
                    )
                    
                    if exit_short:
                        df.at[idx, 'Signal'] = abs(self.position_scale)
                        self._reset_trade_vars()
        
        return df
    
    def _reset_trade_vars(self):
        """Reset all trade-related variables"""
        self.position = 0
        self.entry_price = 0.0
        self.entry_date = None
        self.stop_loss = 0.0
        self.take_profit_1 = 0.0
        self.take_profit_2 = 0.0
        self.trailing_stop = 0.0
        self.position_scale = 1.0