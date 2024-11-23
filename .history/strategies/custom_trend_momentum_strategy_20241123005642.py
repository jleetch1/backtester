import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class CustomTrendMomentumStrategy(BaseStrategy):
    description = """Custom Trend Momentum Strategy
    
    A robust strategy that combines trend identification, momentum confirmation, and volume validation:
    - Identifies the prevailing trend using Moving Averages
    - Confirms momentum with the Relative Strength Index (RSI)
    - Validates signals with On-Balance Volume (OBV)
    - Utilizes Average True Range (ATR) for dynamic stop-loss placement
    
    Parameters:
    - Short MA Period: {} days (fast moving average for trend)
    - Long MA Period: {} days (slow moving average for trend)
    - RSI Period: {} days (momentum indicator)
    - RSI Overbought Threshold: {} (momentum sell threshold)
    - RSI Oversold Threshold: {} (momentum buy threshold)
    - ATR Period: {} days (volatility measure)
    - ATR Multiplier: {} (for stop-loss calculation)
    - OBV Threshold: {}x average volume (volume confirmation)
    """
    
    def __init__(self, initial_capital: float, short_ma: int = 50, long_ma: int = 200,
                 rsi_period: int = 14, rsi_overbought: float = 70,
                 rsi_oversold: float = 30, atr_period: int = 14,
                 atr_multiplier: float = 1.5, obv_threshold: float = 1.2):
        super().__init__(initial_capital)
        self.short_ma = short_ma
        self.long_ma = long_ma
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.obv_threshold = obv_threshold
        self.description = self.description.format(
            short_ma, long_ma, rsi_period, rsi_overbought,
            rsi_oversold, atr_period, atr_multiplier, obv_threshold
        )
        self.stop_loss = 0
        self.take_profit = 0

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Moving Averages for trend identification
        df['MA_short'] = df['Close'].rolling(window=self.short_ma).mean()
        df['MA_long'] = df['Close'].rolling(window=self.long_ma).mean()
        
        # Calculate RSI for momentum
        df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=self.rsi_period).rsi()
        
        # Calculate On-Balance Volume for volume confirmation
        df['OBV'] = ta.volume.OnBalanceVolumeIndicator(close=df['Close'], volume=df['Volume']).on_balance_volume()
        df['OBV_MA'] = df['OBV'].rolling(window=self.short_ma).mean()
        
        # Calculate ATR for dynamic stop-loss
        df['ATR'] = ta.volatility.AverageTrueRange(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.atr_period
        ).average_true_range()
        
        # Generate signals
        df['Signal'] = 0
        
        # Define trend direction
        df['Trend'] = 0
        df.loc[df['MA_short'] > df['MA_long'], 'Trend'] = 1  # Uptrend
        df.loc[df['MA_short'] < df['MA_long'], 'Trend'] = -1  # Downtrend
        
        # Buy Signal
        buy_condition = (
            (df['Trend'] == 1) &  # Uptrend
            (df['RSI'] < self.rsi_oversold) &  # RSI oversold
            (df['OBV'] > df['OBV_MA'] * self.obv_threshold)  # Volume confirmation
        )
        
        # Sell Signal
        sell_condition = (
            (df['Trend'] == -1) &  # Downtrend
            (df['RSI'] > self.rsi_overbought) &  # RSI overbought
            (df['OBV'] < df['OBV_MA'] / self.obv_threshold)  # Volume confirmation
        )
        
        # Apply buy signals
        df.loc[buy_condition, 'Signal'] = 1
        
        # Apply sell signals
        df.loc[sell_condition, 'Signal'] = -1
        
        # Manage open positions with dynamic stop-loss
        for idx, row in df.iterrows():
            if self.position == 0:
                if row['Signal'] == 1:
                    self.entry_price = row['Close']
                    self.stop_loss = self.entry_price - (self.atr_multiplier * row['ATR'])
                    self.take_profit = self.entry_price + (self.atr_multiplier * row['ATR'])
                    self.position = self.get_position_size(row['Close'])
                elif row['Signal'] == -1:
                    self.entry_price = row['Close']
                    self.stop_loss = self.entry_price + (self.atr_multiplier * row['ATR'])
                    self.take_profit = self.entry_price - (self.atr_multiplier * row['ATR'])
                    self.position = self.get_position_size(row['Close'])
            else:
                if self.position > 0:
                    # Long position
                    if row['Low'] <= self.stop_loss or row['Close'] >= self.take_profit:
                        df.at[idx, 'Signal'] = -1  # Sell signal
                        self.position = 0
                        self.entry_price = 0
                        self.stop_loss = 0
                        self.take_profit = 0
                elif self.position < 0:
                    # Short position
                    if row['High'] >= self.stop_loss or row['Close'] <= self.take_profit:
                        df.at[idx, 'Signal'] = 1  # Buy to cover
                        self.position = 0
                        self.entry_price = 0
                        self.stop_loss = 0
                        self.take_profit = 0
        
        return df