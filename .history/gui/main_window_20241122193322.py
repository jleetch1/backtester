from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QDateEdit, QDoubleSpinBox,
                            QTableWidget, QTableWidgetItem, QTabWidget)
from PyQt6.QtCore import Qt, QDate
import sys
from datetime import datetime
from core.data_fetcher import DataFetcher
from core.backtest_engine import BacktestEngine
import os
import importlib.util

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Backtesting Application")
        self.setMinimumSize(1200, 800)
        
        self.init_ui()
        self.load_strategies()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Date range controls
        date_layout = QVBoxLayout()
        date_layout.addWidget(QLabel("Trading Range:"))
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addYears(-1))
        date_layout.addWidget(self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date)
        
        controls_layout.addLayout(date_layout)
        
        # Capital control
        capital_layout = QVBoxLayout()
        capital_layout.addWidget(QLabel("Initial Capital:"))
        self.initial_capital = QDoubleSpinBox()
        self.initial_capital.setRange(0, 1000000000)
        self.initial_capital.setValue(100000)
        capital_layout.addWidget(self.initial_capital)
        
        controls_layout.addLayout(capital_layout)
        
        # Run button
        self.run_button = QPushButton("Run Backtest")
        self.run_button.clicked.connect(self.run_backtest)
        controls_layout.addWidget(self.run_button)
        
        layout.addLayout(controls_layout)
        
        # Results tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
    def load_strategies(self):
        self.strategies = []
        strategies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies')
        
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        for file in os.listdir(strategies_dir):
            if file.endswith('.py') and file != '__init__.py' and file != 'base_strategy.py':
                module_name = f'strategies.{file[:-3]}'
                try:
                    module = importlib.import_module(module_name)
                    
                    for item in dir(module):
                        obj = getattr(module, item)
                        if isinstance(obj, type) and item != 'BaseStrategy':
                            self.strategies.append(obj)
                except ImportError as e:
                    print(f"Error importing {module_name}: {e}")
        
    def run_backtest(self):
        # Clear existing tabs
        while self.tabs.count():
            self.tabs.removeTab(0)
            
        symbols = ['AAPL', 'GOOGL', 'BTC/USDT', 'ETH/USDT']  # Example symbols
        data_fetcher = DataFetcher()
        backtest_engine = BacktestEngine(self.initial_capital.value())
        
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        for symbol in symbols:
            # Create results table
            table = QTableWidget()
            table.setColumnCount(7)
            table.setHorizontalHeaderLabels([
                'Strategy',
                'Net Profit',
                'Total Trades',
                'Win Rate %',
                'Profit Factor',
                'Max Drawdown %',
                'Avg Trade'
            ])
            
            # Get data
            if '/' in symbol:  # Crypto
                data = data_fetcher.get_crypto_data(symbol, start_date, end_date)
            else:  # Stock
                data = data_fetcher.get_stock_data(symbol, start_date, end_date)
                
            # Run strategies
            results = []
            for strategy_class in self.strategies:
                strategy = strategy_class(self.initial_capital.value())
                result = backtest_engine.run_backtest(data, strategy)
                results.append((strategy_class.__name__, result))
                
            # Fill table
            table.setRowCount(len(results))
            for i, (strategy_name, result) in enumerate(results):
                table.setItem(i, 0, QTableWidgetItem(strategy_name))
                table.setItem(i, 1, QTableWidgetItem(f"${result['net_profit']:.2f}"))
                table.setItem(i, 2, QTableWidgetItem(str(result['total_trades'])))
                table.setItem(i, 3, QTableWidgetItem(f"{result['win_rate']:.1f}%"))
                table.setItem(i, 4, QTableWidgetItem(f"{result['profit_factor']:.2f}"))
                table.setItem(i, 5, QTableWidgetItem(f"{result['max_drawdown']:.1f}%"))
                table.setItem(i, 6, QTableWidgetItem(f"${result['avg_trade']:.2f}"))
                
            self.tabs.addTab(table, symbol) 