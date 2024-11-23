from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QDateEdit, QDoubleSpinBox,
                            QTableWidget, QTableWidgetItem, QTabWidget, QLineEdit, QMessageBox, QComboBox, QDialog)
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
        
        self.backtest_engine = BacktestEngine(self.initial_capital.value())
        
        self.init_ui()
        self.load_strategies()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Symbol selection
        symbol_layout = QVBoxLayout()
        symbol_layout.addWidget(QLabel("Symbols:"))
        
        # Stock symbols
        self.stock_symbols = QLineEdit()
        self.stock_symbols.setPlaceholderText("Stock symbols (comma-separated, e.g., AAPL,GOOGL)")
        symbol_layout.addWidget(self.stock_symbols)
        
        # Crypto symbols
        self.crypto_symbols = QLineEdit()
        self.crypto_symbols.setPlaceholderText("Crypto pairs (comma-separated, e.g., BTC/USDT,ETH/USDT)")
        symbol_layout.addWidget(self.crypto_symbols)
        
        controls_layout.addLayout(symbol_layout)
        
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
        
        # Strategy selection layout
        strategy_layout = QVBoxLayout()
        strategy_layout.addWidget(QLabel("Select Strategy:"))

        self.strategy_selection = QComboBox()
        self.strategy_selection.addItem("FlawlessVictoryStrategy")
        # Add other strategies if needed
        strategy_layout.addWidget(self.strategy_selection)

        # Strategy version selection
        self.version_selection = QComboBox()
        self.version_selection.addItems(["1", "2", "3"])
        strategy_layout.addWidget(QLabel("Select Version:"))
        strategy_layout.addWidget(self.version_selection)

        controls_layout.addLayout(strategy_layout)
        
        # Run button
        self.run_button = QPushButton("Run Backtest")
        self.run_button.clicked.connect(self.run_backtest)
        controls_layout.addWidget(self.run_button)
        
        # View trade details button
        self.viewDetailsButton = QPushButton("View Trade Details")
        self.viewDetailsButton.clicked.connect(self.view_trade_details)
        controls_layout.addWidget(self.viewDetailsButton)
        
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
            
        # Get symbols from input fields
        stock_symbols = [s.strip() for s in self.stock_symbols.text().split(',') if s.strip()]
        crypto_symbols = [s.strip() for s in self.crypto_symbols.text().split(',') if s.strip()]
        
        symbols = stock_symbols + crypto_symbols
        
        if not symbols:
            QMessageBox.warning(self, "Warning", "Please enter at least one symbol")
            return
        
        data_fetcher = DataFetcher()
        self.backtest_engine = BacktestEngine(self.initial_capital.value())
        
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        
        for symbol in symbols:
            try:
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
                    if strategy_class.__name__ == "FlawlessVictoryStrategy":
                        version = int(self.version_selection.currentText())
                        strategy = strategy_class(self.initial_capital.value(), version=version)
                    else:
                        strategy = strategy_class(self.initial_capital.value())
                    
                    # Use the instance attribute backtest_engine
                    result = self.backtest_engine.run_backtest(data, strategy, ticker=symbol)
                    results.append((strategy_class.__name__, result))
                    
                # Fill table
                table.setRowCount(len(results))
                for i, (strategy_name, result) in enumerate(results):
                    strategy_item = QTableWidgetItem(strategy_name)
                    
                    # Add tooltip with strategy description
                    for strategy_class in self.strategies:
                        if strategy_class.__name__ == strategy_name:
                            strategy_item.setToolTip(strategy_class.description)
                            break
                    
                    table.setItem(i, 0, strategy_item)
                    table.setItem(i, 1, QTableWidgetItem(f"${result['net_profit']:.2f}"))
                    table.setItem(i, 2, QTableWidgetItem(str(result['total_trades'])))
                    table.setItem(i, 3, QTableWidgetItem(f"{result['win_rate']:.1f}%"))
                    table.setItem(i, 4, QTableWidgetItem(f"{result['profit_factor']:.2f}"))
                    table.setItem(i, 5, QTableWidgetItem(f"{result['max_drawdown']:.1f}%"))
                    table.setItem(i, 6, QTableWidgetItem(f"${result['avg_trade']:.2f}"))
                    
                self.tabs.addTab(table, symbol)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error processing {symbol}: {str(e)}") 

    def view_trade_details(self):
        selected_ticker = self.get_selected_ticker()
        selected_strategy = self.get_selected_strategy()
        
        if not selected_ticker or not selected_strategy:
            QMessageBox.warning(self, "Selection Error", "Please select a ticker and a strategy.")
            return
        
        if self.backtest_engine.has_trades(selected_ticker, selected_strategy):
            trades = self.backtest_engine.get_trade_details(selected_ticker, selected_strategy)
            if trades:
                trade_details_dialog = TradeDetailsDialog(trades)
                trade_details_dialog.exec()
            else:
                QMessageBox.information(self, "No Trades", "There are no simulated trades for the selected ticker and strategy.")
        else:
            QMessageBox.information(self, "No Trades", "There are no simulated trades for the selected ticker and strategy.")

    def get_selected_ticker(self):
        # Get the currently selected symbol from the active tab
        current_tab_index = self.tabs.currentIndex()
        if current_tab_index == -1:
            return None
        symbol = self.tabs.tabText(current_tab_index)
        return symbol

    def get_selected_strategy(self):
        # Get the selected strategy from the table in the active tab
        current_tab = self.tabs.currentWidget()
        if isinstance(current_tab, QTableWidget):
            selected_items = current_tab.selectedItems()
            if not selected_items:
                return None
            # Assuming the first column is the strategy name
            strategy_item = selected_items[0]
            strategy_name = strategy_item.text()
            return strategy_name
        return None

class TradeDetailsDialog(QDialog):
    def __init__(self, trades):
        super().__init__()
        self.setWindowTitle("Trade Details")
        self.setGeometry(100, 100, 600, 400)
        
        # Define the trade keys to display
        trade_keys = ['entry_date', 'entry_price', 'position', 'exit_date', 'exit_price', 'profit']
        
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setRowCount(len(trades))
        self.table.setColumnCount(len(trade_keys))
        self.table.setHorizontalHeaderLabels(trade_keys)
        
        for row, trade in enumerate(trades):
            for col, key in enumerate(trade_keys):
                self.table.setItem(row, col, QTableWidgetItem(str(trade.get(key, 'N/A'))))
        
        layout.addWidget(self.table)
        self.setLayout(layout) 