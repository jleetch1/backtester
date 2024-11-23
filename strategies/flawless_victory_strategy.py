import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class FlawlessVictoryStrategy(BaseStrategy):
    description = """Flawless Victory Strategy
    
    Versions:
    - Version 1:
        - RSI > 42 for buy
        - RSI > 70 for sell
        - Bollinger Bands (20, 1.0)
    - Version 2:
        - RSI > 42 for buy
        - RSI > 76 for sell
        - Bollinger Bands (17, 1.0)
        - Stop Loss: 6.604%
        - Take Profit: 2.328%
    - Version 3:
        - MFI < 60 for buy
        - RSI > 65 and MFI > 64 for sell
        - Bollinger Bands (20, 1.0)
        - Stop Loss: 8.882%
        - Take Profit: 2.317%
    """

    def __init__(self, initial_capital: float, version: int = 1):
        super().__init__(initial_capital)
        self.version = version
        self.v2_stoploss = 6.604
        self.v2_takeprofit = 2.328
        self.v3_stoploss = 8.882
        self.v3_takeprofit = 2.317
        self.entry_price = 0
        self.stop_price = 0
        self.take_profit_price = 0

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        # Calculate indicators
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        df['MFI'] = ta.volume.MFIIndicator(df['High'], df['Low'], df['Close'], df['Volume'], window=14).money_flow_index()
        
        if self.version in [1, 3]:
            bb_window = 20
            bb_dev = 1.0
        elif self.version == 2:
            bb_window = 17
            bb_dev = 1.0
        
        # Calculate Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=bb_window).mean()
        df['BB_std'] = df['Close'].rolling(window=bb_window).std()
        df['BB_upper'] = df['BB_middle'] + bb_dev * df['BB_std']
        df['BB_lower'] = df['BB_middle'] - bb_dev * df['BB_std']
        
        df['Signal'] = 0  # Initialize signal column

        for idx, row in df.iterrows():
            if self.position == 0:
                # No open position
                if self.version == 1:
                    buy_signal = (row['Close'] < row['BB_lower']) and (row['RSI'] > 42)
                    sell_signal = (row['Close'] > row['BB_upper']) and (row['RSI'] > 70)
                    
                    if buy_signal:
                        self.position = self.get_position_size(row['Close'])
                        self.entry_price = row['Close']
                        df.at[idx, 'Signal'] = 1  # Buy signal
                    elif sell_signal:
                        pass  # No shorting

                elif self.version == 2:
                    buy_signal = (row['Close'] < row['BB_lower']) and (row['RSI'] > 42)
                    sell_signal = (row['Close'] > row['BB_upper']) and (row['RSI'] > 76)
                    
                    if buy_signal:
                        self.position = self.get_position_size(row['Close'])
                        self.entry_price = row['Close']
                        self.stop_price = self.entry_price * (1 - self.v2_stoploss / 100)
                        self.take_profit_price = self.entry_price * (1 + self.v2_takeprofit / 100)
                        df.at[idx, 'Signal'] = 1  # Buy signal
                    elif sell_signal:
                        pass  # No shorting

                elif self.version == 3:
                    buy_signal = (row['Close'] < row['BB_lower']) and (row['MFI'] < 60)
                    sell_signal = (row['Close'] > row['BB_upper']) and (row['RSI'] > 65) and (row['MFI'] > 64)
                    
                    if buy_signal:
                        self.position = self.get_position_size(row['Close'])
                        self.entry_price = row['Close']
                        self.stop_price = self.entry_price * (1 - self.v3_stoploss / 100)
                        self.take_profit_price = self.entry_price * (1 + self.v3_takeprofit / 100)
                        df.at[idx, 'Signal'] = 1  # Buy signal
                    elif sell_signal:
                        pass  # No shorting
            else:
                # Manage open position
                if self.version == 1:
                    sell_signal = (row['Close'] > row['BB_upper']) and (row['RSI'] > 70)
                    if sell_signal:
                        df.at[idx, 'Signal'] = -1  # Sell signal

                elif self.version == 2:
                    sell_signal = (row['Close'] > row['BB_upper']) and (row['RSI'] > 76)
                    if sell_signal:
                        df.at[idx, 'Signal'] = -1  # Sell signal
                    else:
                        if row['Low'] <= self.stop_price:
                            df.at[idx, 'Signal'] = -1  # Stop loss
                        elif row['High'] >= self.take_profit_price:
                            df.at[idx, 'Signal'] = -1  # Take profit

                elif self.version == 3:
                    sell_signal = (row['Close'] > row['BB_upper']) and (row['RSI'] > 65) and (row['MFI'] > 64)
                    if sell_signal:
                        df.at[idx, 'Signal'] = -1  # Sell signal
                    else:
                        if row['Low'] <= self.stop_price:
                            df.at[idx, 'Signal'] = -1  # Stop loss
                        elif row['High'] >= self.take_profit_price:
                            df.at[idx, 'Signal'] = -1  # Take profit

                # Reset position if sold
                if df.at[idx, 'Signal'] == -1:
                    self.position = 0
                    self.entry_price = 0
                    self.stop_price = 0
                    self.take_profit_price = 0

        return df