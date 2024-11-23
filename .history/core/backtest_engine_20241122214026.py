import pandas as pd
from typing import List, Dict
from strategies.base_strategy import BaseStrategy
from collections import defaultdict

class BacktestEngine:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.trade_details = defaultdict(list)  # Initialize a defaultdict to store trades per (ticker, strategy)
        self.price_data = {}  # Add this to store price data
        
    def run_backtest(self, data: pd.DataFrame, strategy: BaseStrategy, ticker: str) -> Dict:
        # Store the price data
        self.price_data[ticker] = data
        
        df = strategy.generate_signals(data)
        
        # Initialize results
        position = 0
        capital = self.initial_capital
        trades = []
        entry_price = 0
        
        for idx, row in df.iterrows():
            if row['Signal'] == 1 and position == 0:  # Buy signal
                position = strategy.get_position_size(row['Close'])
                entry_price = row['Close']
                trades.append({
                    'entry_date': idx,
                    'entry_price': entry_price,
                    'position': position,
                    'profit': 0  # Initialize profit
                })
                
            elif row['Signal'] == -1 and position != 0:  # Sell signal
                exit_price = row['Close']
                trade_profit = (exit_price - entry_price) * position
                capital += trade_profit
                
                trades[-1].update({
                    'exit_date': idx,
                    'exit_price': exit_price,
                    'profit': trade_profit
                })
                
                position = 0
        
        # Close any open position at the end
        if position != 0:
            exit_price = df['Close'].iloc[-1]
            trade_profit = (exit_price - entry_price) * position
            capital += trade_profit
            trades[-1].update({
                'exit_date': df.index[-1],
                'exit_price': exit_price,
                'profit': trade_profit
            })
                
        # Store trades for the given ticker and strategy
        strategy_name = strategy.__class__.__name__
        self.trade_details[(ticker, strategy_name)] = trades
            
        return self._calculate_statistics(trades, capital)
    
    def has_trades(self, ticker, strategy_name):
        # Debug print
        print(f"Checking trades for {ticker}, {strategy_name}")
        print(f"Available keys: {self.trade_details.keys()}")
        return bool(self.trade_details.get((ticker, strategy_name), []))
    
    def get_trade_details(self, ticker, strategy_name):
        # Debug print
        print(f"Getting trades for {ticker}, {strategy_name}")
        trades = self.trade_details.get((ticker, strategy_name), [])
        print(f"Found {len(trades)} trades")
        return trades

    def _calculate_statistics(self, trades: List[Dict], final_capital: float) -> Dict:
        if not trades:
            return {
                'net_profit': 0,
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'avg_trade': 0,
                'avg_bars_in_trade': 0
            }
            
        # Only consider closed trades
        closed_trades = [t for t in trades if 'exit_date' in t]
        if not closed_trades:
            return {
                'net_profit': 0,
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'avg_trade': 0,
                'avg_bars_in_trade': 0
            }
            
        winning_trades = [t for t in closed_trades if t['profit'] > 0]
        losing_trades = [t for t in closed_trades if t['profit'] <= 0]
        
        gross_profit = sum(t['profit'] for t in winning_trades)
        gross_loss = abs(sum(t['profit'] for t in losing_trades)) if losing_trades else 1
        
        return {
            'net_profit': final_capital - self.initial_capital,
            'total_trades': len(closed_trades),
            'win_rate': (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0,
            'profit_factor': gross_profit / gross_loss if gross_loss != 0 else float('inf'),
            'max_drawdown': self._calculate_max_drawdown(closed_trades),
            'avg_trade': (final_capital - self.initial_capital) / len(closed_trades) if closed_trades else 0,
            'avg_bars_in_trade': sum((t['exit_date'] - t['entry_date']).days for t in closed_trades) / len(closed_trades) if closed_trades else 0
        }
        
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        if not trades:
            return 0
            
        equity_curve = []
        current_equity = self.initial_capital
        
        for trade in trades:
            current_equity += trade['profit']
            equity_curve.append(current_equity)
            
        max_drawdown = 0
        peak = self.initial_capital
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
            
        return max_drawdown 

    def get_price_data(self, ticker: str) -> pd.DataFrame:
        """Retrieve the price data for a given ticker."""
        return self.price_data.get(ticker)