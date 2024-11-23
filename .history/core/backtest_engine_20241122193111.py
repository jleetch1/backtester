import pandas as pd
from typing import List, Dict
from ..strategies.base_strategy import BaseStrategy

class BacktestEngine:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        
    def run_backtest(self, data: pd.DataFrame, strategy: BaseStrategy) -> Dict:
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
                    'position': position
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
                
        return self._calculate_statistics(trades, capital)
    
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
            
        winning_trades = [t for t in trades if t.get('profit', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit', 0) <= 0]
        
        gross_profit = sum(t['profit'] for t in winning_trades)
        gross_loss = abs(sum(t['profit'] for t in losing_trades))
        
        return {
            'net_profit': final_capital - self.initial_capital,
            'total_trades': len(trades),
            'win_rate': len(winning_trades) / len(trades) * 100,
            'profit_factor': gross_profit / gross_loss if gross_loss != 0 else float('inf'),
            'max_drawdown': self._calculate_max_drawdown(trades),
            'avg_trade': (final_capital - self.initial_capital) / len(trades),
            'avg_bars_in_trade': sum((t['exit_date'] - t['entry_date']).days for t in trades) / len(trades)
        }
        
    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        equity_curve = []
        current_equity = self.initial_capital
        
        for trade in trades:
            current_equity += trade.get('profit', 0)
            equity_curve.append(current_equity)
            
        max_drawdown = 0
        peak = self.initial_capital
        
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
            
        return max_drawdown 