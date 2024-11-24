import pandas as pd
from typing import List, Dict
from strategies.base_strategy import BaseStrategy
from collections import defaultdict
import numpy as np
import scipy.stats as stats

class BacktestEngine:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.trade_details = defaultdict(list)  # Initialize a defaultdict to store trades per (ticker, strategy)
        self.price_data = {}  # Add this to store price data
        
    def run_backtest(self, data: pd.DataFrame, strategy: BaseStrategy, ticker: str) -> Dict:
        try:
            print(f"\nStarting backtest for {ticker} with {strategy.__class__.__name__}")
            print(f"Data shape: {data.shape}")
            
            # Store the price data
            self.price_data[ticker] = data
            
            # Generate signals
            df = strategy.generate_signals(data)
            print(f"Signals generated. Shape: {df.shape}")
            
            # Initialize results
            position = 0
            capital = strategy.initial_capital
            trades = []
            entry_price = 0
            
            print(f"Processing {len(df)} rows for trades")
            trade_count = 0
            
            for idx, row in df.iterrows():
                if row['Signal'] == 1 and position == 0:
                    trade_count += 1
                    position = strategy.get_position_size(row['Close'])
                    entry_price = row['Close']
                    trades.append({
                        'entry_date': idx,
                        'entry_price': entry_price,
                        'position': position,
                        'profit': 0
                    })
                    
                elif row['Signal'] == -1 and position != 0:
                    trade_count += 1
                    exit_price = row['Close']
                    trade_profit = (exit_price - entry_price) * position
                    capital += trade_profit
                    
                    trades[-1].update({
                        'exit_date': idx,
                        'exit_price': exit_price,
                        'profit': trade_profit
                    })
                    
                    position = 0
            
            print(f"Completed processing. Found {trade_count} trades")
            return self._calculate_statistics(trades, capital)
            
        except Exception as e:
            print(f"Error in backtest engine: {str(e)}")
            print(f"Error occurred at line: {e.__traceback__.tb_lineno}")
            return self._get_empty_stats()
    
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
            return self._get_empty_stats()
            
        closed_trades = [t for t in trades if 'exit_date' in t]
        if not closed_trades:
            return self._get_empty_stats()
            
        winning_trades = [t for t in closed_trades if t['profit'] > 0]
        losing_trades = [t for t in closed_trades if t['profit'] <= 0]
        
        # Basic calculations
        gross_profit = sum(t['profit'] for t in winning_trades)
        gross_loss = abs(sum(t['profit'] for t in losing_trades)) if losing_trades else 1
        
        # Calculate returns
        total_return = (final_capital - self.initial_capital) / self.initial_capital * 100
        total_days = (trades[-1]['exit_date'] - trades[0]['entry_date']).days if trades else 0
        
        # Return metrics
        annualized_return = ((final_capital / self.initial_capital) ** (365 / total_days) - 1) * 100 if total_days > 0 else 0
        cagr = self._calculate_cagr(trades, final_capital)
        monthly_returns = self._calculate_monthly_returns(trades)
        
        # Risk metrics
        returns_series = self.calculate_returns_series(trades)
        volatility = returns_series.std() * (252 ** 0.5) * 100
        
        # Risk-adjusted returns
        risk_free_rate = 0.02  # Assuming 2% risk-free rate
        excess_returns = returns_series.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_returns / (returns_series.std() * (252 ** 0.5)) if returns_series.std() != 0 else 0
        
        # Sortino ratio
        negative_returns = returns_series[returns_series < 0]
        downside_deviation = negative_returns.std() * (252 ** 0.5) if not negative_returns.empty else 0
        sortino_ratio = excess_returns / downside_deviation if downside_deviation != 0 else 0
        
        # Calmar ratio
        max_dd = self._calculate_max_drawdown(closed_trades)
        calmar_ratio = annualized_return / max_dd if max_dd != 0 else 0
        
        # Trade analysis
        avg_win = sum(t['profit'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['profit'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0
        expectancy = (avg_win * win_rate) - (abs(avg_loss) * (1 - win_rate))
        
        # Value at Risk calculations
        var_95 = self._calculate_var(returns_series, 0.95)
        var_99 = self._calculate_var(returns_series, 0.99)
        cvar_95 = self._calculate_cvar(returns_series, 0.95)
        
        return {
            'net_profit': final_capital - self.initial_capital,
            'total_trades': len(closed_trades),
            'win_rate': win_rate * 100,
            'profit_factor': gross_profit / gross_loss if gross_loss != 0 else float('inf'),
            'max_drawdown': max_dd,
            'avg_trade': (final_capital - self.initial_capital) / len(closed_trades) if closed_trades else 0,
            'avg_bars_in_trade': sum((t['exit_date'] - t['entry_date']).days for t in closed_trades) / len(closed_trades) if closed_trades else 0,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'cagr': cagr,
            'monthly_returns': monthly_returns,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'expectancy': expectancy,
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'winning_trades_count': len(winning_trades),
            'losing_trades_count': len(losing_trades),
            'largest_win': max((t['profit'] for t in winning_trades), default=0),
            'largest_loss': min((t['profit'] for t in losing_trades), default=0),
            'avg_trade_duration': sum((t['exit_date'] - t['entry_date']).days for t in closed_trades) / len(closed_trades) if closed_trades else 0,
            'profit_distribution': self._calculate_profit_distribution(trades),
            'market_environment_performance': self._analyze_market_environment(trades)
        }

    def _get_empty_stats(self):
        """Return empty statistics dictionary with zero values"""
        return {
            'net_profit': 0,
            'total_trades': 0,
            'win_rate': 0,
            # ... (all other metrics initialized to 0)
        }

    def _calculate_cagr(self, trades: List[Dict], final_capital: float) -> float:
        if not trades:
            return 0
        years = (trades[-1]['exit_date'] - trades[0]['entry_date']).days / 365
        if years == 0:
            return 0
        return ((final_capital / self.initial_capital) ** (1/years) - 1) * 100

    def _calculate_monthly_returns(self, trades: List[Dict]) -> Dict:
        """Calculate monthly returns from trades"""
        monthly_returns = {}
        current_equity = self.initial_capital
        
        for trade in trades:
            month_key = trade['exit_date'].strftime('%Y-%m')
            if month_key not in monthly_returns:
                monthly_returns[month_key] = 0
            monthly_returns[month_key] += trade['profit']
            
        return monthly_returns

    def _calculate_var(self, returns_series: pd.Series, confidence_level: float) -> float:
        """Calculate Value at Risk"""
        if returns_series.empty:
            return 0
        return abs(returns_series.quantile(1 - confidence_level))

    def _calculate_cvar(self, returns_series: pd.Series, confidence_level: float) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if returns_series.empty:
            return 0
        var = self._calculate_var(returns_series, confidence_level)
        return abs(returns_series[returns_series <= -var].mean())

    def _calculate_profit_distribution(self, trades: List[Dict]) -> Dict:
        """Analyze profit distribution of trades"""
        if not trades:
            return {}
            
        profits = [t['profit'] for t in trades]
        return {
            'mean': np.mean(profits),
            'median': np.median(profits),
            'std': np.std(profits),
            'skew': stats.skew(profits),
            'kurtosis': stats.kurtosis(profits)
        }

    def _analyze_market_environment(self, trades: List[Dict]) -> Dict:
        """Analyze performance in different market environments"""
        # This is a simplified version - you might want to enhance this
        if not trades:
            return {}
            
        # Classify trades into market environments (simplified)
        bull_market_trades = []
        bear_market_trades = []
        sideways_market_trades = []
        
        # You would need to implement logic to classify trades
        # This is just a placeholder
        return {
            'bull_market': {
                'trade_count': len(bull_market_trades),
                'win_rate': 0,  # Calculate this
                'avg_profit': 0  # Calculate this
            },
            'bear_market': {
                'trade_count': len(bear_market_trades),
                'win_rate': 0,
                'avg_profit': 0
            },
            'sideways_market': {
                'trade_count': len(sideways_market_trades),
                'win_rate': 0,
                'avg_profit': 0
            }
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

    def calculate_returns_series(self, trades: List[Dict]) -> pd.Series:
        """Calculate daily returns series from trades."""
        equity_curve = pd.Series(index=[t['exit_date'] for t in trades], data=self.initial_capital)
        current_equity = self.initial_capital
        for trade in trades:
            current_equity += trade['profit']
            equity_curve.at[trade['exit_date']] = current_equity

        returns = equity_curve.pct_change().dropna()
        return returns