import pandas as pd
from strategies.base_strategy import BaseStrategy
import ta

class KeltnerChannelStrategy(BaseStrategy):
    description = """Keltner Channel Strategy
    
    Uses Keltner Channels to identify breakouts:
    - Buy when price breaks above the upper channel
    - Sell when price breaks below the lower channel
    
    Parameters:
    - Window: {} periods
    - ATR Window: {} periods
    - ATR Multiplier: {}
    """
    
    def __init__(self, initial_capital: float, window: int = 20, 
                 atr_window: int = 10, atr_multiplier: float = 2.0):
        super().__init__(initial_capital)
        self.window = window
        self.atr_window = atr_window
        self.multiplier = atr_multiplier
        self.description = self.description.format(
            window, atr_window, atr_multiplier
        )
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        
        # Calculate Keltner Channels
        indicator_kc = ta.volatility.KeltnerChannel(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.window,
            window_atr=self.atr_window,
            multiplier=self.multiplier
        )
        
        df['KC_Upper'] = indicator_kc.keltner_channel_hband()
        df['KC_Middle'] = indicator_kc.keltner_channel_mband()
        df['KC_Lower'] = indicator_kc.keltner_channel_lband()
        
        # Generate signals
        df['Signal'] = 0
        
        # Buy signal when price breaks above upper channel
        df.loc[df['Close'] > df['KC_Upper'], 'Signal'] = 1
        
        # Sell signal when price breaks below lower channel
        df.loc[df['Close'] < df['KC_Lower'], 'Signal'] = -1
        
        return df 