from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QDateEdit, QDoubleSpinBox,
                            QTableWidget, QTableWidgetItem, QTabWidget, QLineEdit, QMessageBox, QComboBox, QDialog, QSplitter, QCheckBox, QMenu, QProgressBar, QStatusBar, QApplication)
from PyQt6.QtCore import Qt, QDate
import sys
from datetime import datetime
from core.data_fetcher import DataFetcher
from core.backtest_engine import BacktestEngine
import os
import importlib.util
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd
from strategies.base_strategy import PositionSizingMethod
from core.symbol_manager import SymbolManager
from PyQt6.QtGui import QFocusEvent
from typing import List
import json

class NumberTableWidgetItem(QTableWidgetItem):
    def __init__(self, value):
        super().__init__(str(value))
        self.value = value

    def __lt__(self, other):
        if isinstance(other, NumberTableWidgetItem):
            return self.value < other.value
        return super().__lt__(other)

class PersistentMenu(QMenu):
    def mouseReleaseEvent(self, e):
        action = self.activeAction()
        if action and action.isCheckable():
            action.trigger()
            # Prevent menu from closing
            e.ignore()
        elif action and (action.text() == "Select All" or action.text() == "Deselect All"):
            action.trigger()
            # Prevent menu from closing
            e.ignore()
        else:
            super().mouseReleaseEvent(e)

class SymbolLineEdit(QLineEdit):
    def __init__(self, symbol_type: str, symbol_manager: SymbolManager, parent=None):
        super().__init__(parent)
        self.symbol_type = symbol_type
        self.symbol_manager = symbol_manager
        self.menu = None
        
        # Create layout for the widget
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create container widget
        self.container = QWidget(parent)
        self.container.setLayout(self.layout)
        
        # Add line edit to layout
        self.line_edit = QLineEdit()
        self.layout.addWidget(self.line_edit)
        
        # Add dropdown button
        self.dropdown_button = QPushButton("▼")
        self.dropdown_button.setMaximumWidth(20)
        self.dropdown_button.clicked.connect(self.showSymbolMenu)
        self.layout.addWidget(self.dropdown_button)
    
    def text(self):
        return self.line_edit.text()
    
    def setText(self, text):
        self.line_edit.setText(text)
    
    def setPlaceholderText(self, text):
        self.line_edit.setPlaceholderText(text)
    
    def showSymbolMenu(self):
        if self.menu is not None:
            self.menu.close()
        
        self.menu = PersistentMenu(self)
        
        # Get symbols based on type
        symbols = (self.symbol_manager.get_stock_symbols() 
                  if self.symbol_type == "stock" 
                  else self.symbol_manager.get_crypto_symbols())
        
        # Add recent symbols
        if symbols:
            for symbol in symbols:
                action = self.menu.addAction(symbol)
                action.triggered.connect(lambda checked, s=symbol: self.addSymbol(s))
        else:
            # Show placeholder text if no symbols
            no_symbols = self.menu.addAction("No recent symbols")
            no_symbols.setEnabled(False)
        
        # Position menu below the line edit
        self.menu.exec(self.dropdown_button.mapToGlobal(self.dropdown_button.rect().bottomLeft()))
    
    def addSymbol(self, symbol: str):
        """Add selected symbol to current text"""
        current_text = self.line_edit.text().strip()
        symbols = [s.strip() for s in current_text.split(',') if s.strip()]
        
        if symbol not in symbols:
            symbols.append(symbol)
            self.line_edit.setText(', '.join(symbols))

class MainWindow(QMainWindow):
    STOCK_TIMEFRAME_LIMITS = {
        '1m': 7,
        '2m': 60,
        '5m': 60,
        '15m': 60,
        '30m': 60,
        '60m': 730,
        '1h': 730,
        '1d': float('inf'),
        '1wk': float('inf'),
        '1mo': float('inf')
    }
    
    CRYPTO_TIMEFRAME_LIMITS = [
        ('1m', float('inf')),
        ('3m', float('inf')),
        ('5m', float('inf')),
        ('15m', float('inf')),
        ('30m', float('inf')),
        ('1h', float('inf')),
        ('2h', float('inf')),
        ('4h', float('inf')),
        ('6h', float('inf')),
        ('8h', float('inf')),
        ('12h', float('inf')),
        ('1d', float('inf')),
        ('3d', float('inf')),
        ('1w', float('inf')),
        ('1M', float('inf'))
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Backtesting Application")
        self.setMinimumSize(1200, 800)
        
        # Create status bar and progress bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.progressBar = QProgressBar()
        self.progressBar.setMaximumWidth(300)
        self.progressBar.hide()  # Hide initially
        self.statusBar.addPermanentWidget(self.progressBar)
        
        self.statusLabel = QLabel()
        self.statusBar.addWidget(self.statusLabel)
        
        # Initialize UI first
        self.init_ui()
        # Then initialize backtest_engine with the now-existing initial_capital
        self.backtest_engine = BacktestEngine(self.initial_capital.value())
        
        self.load_strategies()
        
        self.sort_order_state = {}  # Add this to track sort orders
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Initialize symbol manager
        self.symbol_manager = SymbolManager()
        
        # Symbol selection
        symbol_layout = QVBoxLayout()
        symbol_layout.addWidget(QLabel("Symbols:"))
        
        # Stock symbols container
        stock_container = QWidget()
        stock_layout = QHBoxLayout(stock_container)
        stock_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stock_symbols = QLineEdit()
        self.stock_symbols.setPlaceholderText("Stock symbols (comma-separated, e.g., AAPL,GOOGL)")
        stock_layout.addWidget(self.stock_symbols)
        
        stock_dropdown = QPushButton("▼")
        stock_dropdown.setMaximumWidth(20)
        stock_dropdown.clicked.connect(lambda: self.show_symbol_menu("stock"))
        stock_layout.addWidget(stock_dropdown)
        
        symbol_layout.addWidget(stock_container)
        
        # Crypto symbols container
        crypto_container = QWidget()
        crypto_layout = QHBoxLayout(crypto_container)
        crypto_layout.setContentsMargins(0, 0, 0, 0)
        
        self.crypto_symbols = QLineEdit()
        self.crypto_symbols.setPlaceholderText("Crypto pairs (comma-separated, e.g., BTC/USDT,ETH/USDT)")
        crypto_layout.addWidget(self.crypto_symbols)
        
        crypto_dropdown = QPushButton("▼")
        crypto_dropdown.setMaximumWidth(20)
        crypto_dropdown.clicked.connect(lambda: self.show_symbol_menu("crypto"))
        crypto_layout.addWidget(crypto_dropdown)
        
        symbol_layout.addWidget(crypto_container)
        
        controls_layout.addLayout(symbol_layout)
        
        # Timeframe selection
        timeframe_layout = QVBoxLayout()
        timeframe_layout.addWidget(QLabel("Timeframe:"))
        self.timeframe_selection = QComboBox()
        self.timeframe_selection.addItems(DataFetcher.get_available_timeframes('stock'))
        timeframe_layout.addWidget(self.timeframe_selection)
        controls_layout.addLayout(timeframe_layout)
        
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
        
        # Position sizing controls
        position_sizing_layout = QVBoxLayout()
        position_sizing_layout.addWidget(QLabel("Position Sizing:"))
        
        # Method selection
        self.position_method = QComboBox()
        self.position_method.addItems([method.value for method in PositionSizingMethod])
        position_sizing_layout.addWidget(self.position_method)
        
        # Size value input
        self.position_size = QDoubleSpinBox()
        self.position_size.setRange(0, 1000000000)
        self.position_size.setValue(100)  # Default to 100% equity
        position_sizing_layout.addWidget(self.position_size)
        
        # Add tooltip explaining current value meaning
        self.position_method.currentTextChanged.connect(self.update_position_size_tooltip)
        self.update_position_size_tooltip(self.position_method.currentText())
        
        controls_layout.addLayout(position_sizing_layout)
        
        # Strategy selection layout
        strategy_layout = QVBoxLayout()
        strategy_layout.addWidget(QLabel("Select Strategies:"))

        # Create a button that will show the menu
        self.strategy_dropdown = QPushButton("Select Strategies ▼")
        self.strategy_dropdown.clicked.connect(self.show_strategy_menu)
        strategy_layout.addWidget(self.strategy_dropdown)

        # Initialize strategy checkboxes dictionary
        self.strategy_checkboxes = {}

        # Version selection remains the same
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
        
        # Create a vertical layout for additional controls
        additional_controls_layout = QVBoxLayout()

        # Add checkbox for report generation
        self.generate_report_checkbox = QCheckBox("Generate Detailed Report")
        additional_controls_layout.addWidget(self.generate_report_checkbox)

        # Add the additional controls layout to the main controls layout
        controls_layout.addLayout(additional_controls_layout)

        layout.addLayout(controls_layout)
        
        # Results tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        self.start_date.dateChanged.connect(self.on_date_changed)
        self.end_date.dateChanged.connect(self.on_date_changed)
        
        # Add timeframe selection change handler
        self.timeframe_selection.currentTextChanged.connect(self.on_timeframe_changed)
        
    def load_strategies(self):
        """Load available strategies and create checkboxes"""
        self.strategies = []
        strategies_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'strategies')
        
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        # Clear existing checkboxes
        self.strategy_checkboxes.clear()
        
        for file in os.listdir(strategies_dir):
            if file.endswith('.py') and file != '__init__.py' and file != 'base_strategy.py':
                module_name = f'strategies.{file[:-3]}'
                try:
                    module = importlib.import_module(module_name)
                    
                    for item in dir(module):
                        obj = getattr(module, item)
                        if isinstance(obj, type) and item != 'BaseStrategy':
                            # Create hidden checkbox for the strategy
                            checkbox = QCheckBox(item)
                            checkbox.setChecked(True)  # Default to checked
                            self.strategy_checkboxes[item] = checkbox
                            self.strategies.append(obj)
                except ImportError as e:
                    print(f"Error importing {module_name}: {e}")
        
        # Set initial button text
        selected_count = len(self.strategy_checkboxes)
        self.strategy_dropdown.setText(f"Strategies ({selected_count}/{selected_count}) ▼")

    def run_backtest(self):
        # Get selected strategies
        selected_strategies = [strategy for strategy in self.strategies 
                             if self.strategy_checkboxes[strategy.__name__].isChecked()]
        
        if not selected_strategies:
            QMessageBox.warning(self, "Warning", "Please select at least one strategy")
            return
            
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
        selected_timeframe = self.timeframe_selection.currentText()
        
        # Validate timeframe selection against date range
        if stock_symbols:
            days_difference = (end_date - start_date).days
            
            timeframe_limits = {
                '1m': 7,
                '2m': 60,
                '5m': 60,
                '15m': 60,
                '30m': 60,
                '60m': 730,
                '1h': 730,
                '1d': float('inf'),
                '1wk': float('inf'),
                '1mo': float('inf')
            }
            
            if days_difference > timeframe_limits.get(selected_timeframe, 0):
                QMessageBox.warning(
                    self, 
                    "Invalid Timeframe",
                    f"Selected timeframe '{selected_timeframe}' is limited to "
                    f"{timeframe_limits[selected_timeframe]} days of historical data.\n"
                    f"Please adjust your date range or select a different timeframe."
                )
                return
        
        # Get position sizing settings
        method = PositionSizingMethod(self.position_method.currentText())
        size_value = self.position_size.value()
        
        # Create a dictionary to store aggregated results for each strategy
        aggregated_results = {}
        
        # Keep track of failed symbols
        failed_symbols = []
        
        # Setup progress tracking
        total_operations = len(symbols)
        self.progressBar.setMaximum(total_operations)
        self.progressBar.setValue(0)
        self.progressBar.show()
        
        for index, symbol in enumerate(symbols):
            # Update status
            self.statusLabel.setText(f"Processing {symbol}...")
            self.progressBar.setValue(index)
            
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
                
                # Get data with selected timeframe
                try:
                    if '/' in symbol:  # Crypto
                        data = data_fetcher.get_crypto_data(symbol, start_date, end_date, interval=selected_timeframe)
                    else:  # Stock
                        data = data_fetcher.get_stock_data(symbol, start_date, end_date, interval=selected_timeframe)
                    
                    if data.empty:
                        failed_symbols.append(symbol)
                        continue
                    
                except Exception as e:
                    failed_symbols.append(symbol)
                    continue
                    
                # Run only selected strategies
                results = []
                for strategy_class in selected_strategies:
                    if strategy_class.__name__ == "FlawlessVictoryStrategy":
                        version = int(self.version_selection.currentText())
                        strategy = strategy_class(self.initial_capital.value(), version=version)
                    else:
                        strategy = strategy_class(self.initial_capital.value())
                    
                    # Store position sizing settings in the strategy instance
                    strategy.position_sizing_method = method
                    strategy.position_size_value = size_value
                    
                    # Use the instance attribute backtest_engine
                    result = self.backtest_engine.run_backtest(data, strategy, ticker=symbol)
                    results.append((strategy_class.__name__, result))
                    
                    # Aggregate results
                    if strategy_class.__name__ not in aggregated_results:
                        aggregated_results[strategy_class.__name__] = {
                            'net_profit': 0,
                            'total_trades': 0,
                            'winning_trades': 0,
                            'total_symbols': 0,
                            'max_drawdown': 0,
                            'profit_factor': 0,
                            'symbols': [],
                            'strategy_instances': [],
                            'total_return': 0,
                            'annualized_return': 0,
                            'volatility': 0,
                            'sharpe_ratio': 0,
                            'sortino_ratio': 0,
                            'avg_drawdown': 0,
                            'win_rate': 0,
                            'avg_trade_duration': 0
                        }
                    
                    agg = aggregated_results[strategy_class.__name__]
                    agg['net_profit'] += result['net_profit']
                    agg['total_trades'] += result['total_trades']
                    agg['winning_trades'] += (result['win_rate'] * result['total_trades'] / 100)
                    agg['total_symbols'] += 1
                    agg['max_drawdown'] = max(agg['max_drawdown'], result['max_drawdown'])
                    agg['profit_factor'] = (agg['profit_factor'] * (len(agg['symbols'])) + result['profit_factor']) / (len(agg['symbols']) + 1)
                    agg['total_return'] = (agg['total_return'] * (len(agg['symbols'])) + result['total_return']) / (len(agg['symbols']) + 1)
                    agg['annualized_return'] = (agg['annualized_return'] * (len(agg['symbols'])) + result['annualized_return']) / (len(agg['symbols']) + 1)
                    agg['volatility'] = (agg['volatility'] * (len(agg['symbols'])) + result['volatility']) / (len(agg['symbols']) + 1)
                    agg['sharpe_ratio'] = (agg['sharpe_ratio'] * (len(agg['symbols'])) + result['sharpe_ratio']) / (len(agg['symbols']) + 1)
                    agg['sortino_ratio'] = (agg['sortino_ratio'] * (len(agg['symbols'])) + result['sortino_ratio']) / (len(agg['symbols']) + 1)
                    agg['win_rate'] = (agg['win_rate'] * (len(agg['symbols'])) + result['win_rate']) / (len(agg['symbols']) + 1)
                    agg['avg_trade_duration'] = (agg['avg_trade_duration'] * (len(agg['symbols'])) + result.get('avg_bars_in_trade', 0)) / (len(agg['symbols']) + 1)
                    agg['symbols'].append(symbol)
                    agg['strategy_instances'].append(strategy)
                    
                # Fill table
                table.setRowCount(len(results))
                for i, (strategy_name, result) in enumerate(results):
                    # Strategy name (text)
                    strategy_item = QTableWidgetItem(strategy_name)
                    strategy_item.setData(Qt.ItemDataRole.DisplayRole, strategy_name)
                    table.setItem(i, 0, strategy_item)
                    
                    # Net Profit (numerical)
                    net_profit_item = QTableWidgetItem()
                    net_profit_item.setData(Qt.ItemDataRole.DisplayRole, f"${result['net_profit']:.2f}")
                    net_profit_item.setData(Qt.ItemDataRole.EditRole, float(result['net_profit']))
                    table.setItem(i, 1, net_profit_item)
                    
                    # Total Trades (numerical)
                    total_trades = int(result['total_trades'])
                    trades_item = NumberTableWidgetItem(total_trades)
                    table.setItem(i, 2, trades_item)
                    
                    # Win Rate (numerical)
                    win_rate_item = QTableWidgetItem()
                    win_rate_item.setData(Qt.ItemDataRole.DisplayRole, f"{result['win_rate']:.1f}%")
                    win_rate_item.setData(Qt.ItemDataRole.EditRole, float(result['win_rate']))
                    table.setItem(i, 3, win_rate_item)
                    
                    # Profit Factor (numerical)
                    pf_item = QTableWidgetItem()
                    pf_item.setData(Qt.ItemDataRole.DisplayRole, f"{result['profit_factor']:.2f}")
                    pf_item.setData(Qt.ItemDataRole.EditRole, float(result['profit_factor']))
                    table.setItem(i, 4, pf_item)
                    
                    # Max Drawdown (numerical)
                    dd_item = QTableWidgetItem()
                    dd_item.setData(Qt.ItemDataRole.DisplayRole, f"{result['max_drawdown']:.1f}%")
                    dd_item.setData(Qt.ItemDataRole.EditRole, float(result['max_drawdown']))
                    table.setItem(i, 5, dd_item)
                    
                    # Avg Trade (numerical)
                    avg_trade_item = QTableWidgetItem()
                    avg_trade_item.setData(Qt.ItemDataRole.DisplayRole, f"${result['avg_trade']:.2f}")
                    avg_trade_item.setData(Qt.ItemDataRole.EditRole, float(result['avg_trade']))
                    table.setItem(i, 6, avg_trade_item)
                    
                # Enable sorting on the table
                table.setSortingEnabled(True)
                
                # Connect the header click to the custom handler
                table.horizontalHeader().sectionClicked.connect(lambda section, tbl=table: self.handle_header_click(section, tbl))
                
                self.tabs.addTab(table, symbol)
            except Exception as e:
                failed_symbols.append(symbol)
                continue
            
            # Process Qt events to keep UI responsive
            QApplication.instance().processEvents()
        
        # Update progress bar to completion
        self.progressBar.setValue(total_operations)
        self.statusLabel.setText("Backtesting complete")
        
        # Create summary tab
        self.create_summary_tab(aggregated_results)
        
        # After successful backtest, update symbol history
        successful_stocks = [s for s in stock_symbols if s not in failed_symbols]
        successful_cryptos = [s for s in crypto_symbols if s not in failed_symbols]
        self.update_symbol_history(successful_stocks, successful_cryptos)
        
        # Show failed symbols message if any
        if failed_symbols:
            QMessageBox.information(
                self,
                "Unavailable Symbols",
                f"The following symbols could not be processed:\n{', '.join(failed_symbols)}\n\n"
                "This might be due to invalid symbols or data availability issues."
            )
        
        # Hide progress bar after completion
        self.progressBar.hide()
        self.statusLabel.clear()

        # After backtesting is complete
        if self.generate_report_checkbox.isChecked():
            self.generate_detailed_report(aggregated_results)

    def create_summary_tab(self, aggregated_results):
        """Create a summary tab showing performance across all symbols"""
        summary_table = QTableWidget()
        summary_table.setColumnCount(8)
        summary_table.setHorizontalHeaderLabels([
            'Strategy',
            'Net Profit',
            'Total Trades',
            'Win Rate %',
            'Profit Factor',
            'Max Drawdown %',
            'Symbols Tested',
            'Symbols List'
        ])
        
        # Add rows for each strategy
        summary_table.setRowCount(len(aggregated_results))
        for i, (strategy_name, results) in enumerate(aggregated_results.items()):
            # Strategy name
            strategy_item = QTableWidgetItem(strategy_name)
            summary_table.setItem(i, 0, strategy_item)
            
            # Net Profit
            net_profit_item = QTableWidgetItem()
            net_profit_item.setData(Qt.ItemDataRole.DisplayRole, f"${results['net_profit']:,.2f}")
            net_profit_item.setData(Qt.ItemDataRole.EditRole, float(results['net_profit']))
            summary_table.setItem(i, 1, net_profit_item)
            
            # Total Trades
            total_trades = int(results['total_trades'])
            trades_item = NumberTableWidgetItem(total_trades)
            summary_table.setItem(i, 2, trades_item)
            
            # Win Rate
            if results['total_trades'] > 0:
                win_rate = (results['winning_trades'] / results['total_trades']) * 100
                win_rate_item = QTableWidgetItem()
                win_rate_item.setData(Qt.ItemDataRole.DisplayRole, f"{win_rate:.1f}%")
                win_rate_item.setData(Qt.ItemDataRole.EditRole, float(win_rate))
            else:
                win_rate_item = QTableWidgetItem("N/A")
            summary_table.setItem(i, 3, win_rate_item)
            
            # Profit Factor
            pf_item = QTableWidgetItem()
            pf_item.setData(Qt.ItemDataRole.DisplayRole, f"{results['profit_factor']:.2f}")
            pf_item.setData(Qt.ItemDataRole.EditRole, float(results['profit_factor']))
            summary_table.setItem(i, 4, pf_item)
            
            # Max Drawdown
            dd_item = QTableWidgetItem()
            dd_item.setData(Qt.ItemDataRole.DisplayRole, f"{results['max_drawdown']:.1f}%")
            dd_item.setData(Qt.ItemDataRole.EditRole, float(results['max_drawdown']))
            summary_table.setItem(i, 5, dd_item)
            
            # Number of symbols tested
            symbols_count_item = QTableWidgetItem()
            symbols_count_item.setData(Qt.ItemDataRole.DisplayRole, str(results['total_symbols']))
            symbols_count_item.setData(Qt.ItemDataRole.EditRole, int(results['total_symbols']))
            summary_table.setItem(i, 6, symbols_count_item)
            
            # List of symbols (text)
            symbols_item = QTableWidgetItem(", ".join(results['symbols']))
            symbols_item.setToolTip(", ".join(results['symbols']))
            summary_table.setItem(i, 7, symbols_item)
            
            # Color coding based on performance
            if results['net_profit'] > 0:
                net_profit_item.setBackground(Qt.GlobalColor.green)
            else:
                net_profit_item.setBackground(Qt.GlobalColor.red)
        
        # Enable sorting on the summary table
        summary_table.setSortingEnabled(True)
        
        # Connect the header click to the custom handler
        summary_table.horizontalHeader().sectionClicked.connect(lambda section, tbl=summary_table: self.handle_header_click(section, tbl))
        
        # Auto-adjust column widths
        summary_table.resizeColumnsToContents()
        
        # Add the summary tab
        self.tabs.insertTab(0, summary_table, "Summary")  # Insert at the beginning
        self.tabs.setCurrentIndex(0)  # Show the summary tab

    def view_trade_details(self):
        selected_ticker = self.get_selected_ticker()
        selected_strategy = self.get_selected_strategy()
        
        if not selected_ticker or not selected_strategy:
            QMessageBox.warning(self, "Selection Error", "Please select a strategy row in the results table.")
            return
        
        trades = self.backtest_engine.get_trade_details(selected_ticker, selected_strategy)
        if trades:
            # Get the price data for the selected ticker
            price_data = self.backtest_engine.get_price_data(selected_ticker)
            if price_data is not None:
                trade_details_dialog = TradeDetailsDialog(trades, price_data)
                trade_details_dialog.exec()
            else:
                QMessageBox.warning(self, "Error", "Could not retrieve price data for the selected ticker.")
        else:
            QMessageBox.information(self, "No Trades", 
                f"No trades found for {selected_ticker} with {selected_strategy}")

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
            selected_rows = current_tab.selectedItems()
            if selected_rows:
                # Get the strategy name from the first column (index 0) of the selected row
                row = selected_rows[0].row()
                strategy_name = current_tab.item(row, 0).text()
                return strategy_name
        return None

    def update_timeframe_options(self):
        """Update timeframe options while preserving user selection if possible"""
        stock_symbols = self.stock_symbols.text().strip()
        crypto_symbols = self.crypto_symbols.text().strip()
        
        # Store current selection before clearing
        current_selection = self.timeframe_selection.currentText()
        
        # Clear current items
        self.timeframe_selection.clear()
        
        # Calculate date range
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        days_difference = (end_date - start_date).days
        
        if crypto_symbols and not stock_symbols:
            # For crypto only - all timeframes available
            timeframes = [tf for tf, _ in self.CRYPTO_TIMEFRAME_LIMITS]
            self.timeframe_selection.addItems(timeframes)
            # Restore previous selection if it was crypto, otherwise use 1m
            if current_selection in timeframes:
                self.timeframe_selection.setCurrentText(current_selection)
            else:
                self.timeframe_selection.setCurrentText('1m')
        else:
            # Get available timeframes based on date range
            available_timeframes = [tf for tf, limit in self.STOCK_TIMEFRAME_LIMITS.items() 
                                  if days_difference <= limit]
            
            self.timeframe_selection.addItems(available_timeframes)
            
            # Try to restore previous selection if valid
            if current_selection in available_timeframes:
                self.timeframe_selection.setCurrentText(current_selection)
            else:
                # Find the most granular available timeframe
                self.timeframe_selection.setCurrentText(available_timeframes[0])

    def validate_date_range(self):
        """Validate date range and show appropriate warnings/info"""
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        days_difference = (end_date - start_date).days
        
        stock_symbols = self.stock_symbols.text().strip()
        message = ""
        
        if stock_symbols:
            if days_difference <= 7:
                message = "Using 1-minute data for maximum granularity"
            elif days_difference <= 60:
                message = "Using 5-minute data (1-minute data only available for 7 days or less)"
            elif days_difference <= 730:
                message = "Using hourly data (minute data only available for 60 days or less)"
            else:
                message = "Using daily data (hourly data only available for 730 days or less)"
            
            QMessageBox.information(self, "Data Granularity", message)

    def on_date_changed(self):
        """Handle date change events"""
        self.update_timeframe_options()
        # Only show validation message if user hasn't explicitly selected a timeframe
        if not hasattr(self, '_user_selected_timeframe'):
            self.validate_date_range()

    def on_timeframe_changed(self, timeframe):
        """Handle user timeframe selection"""
        self._user_selected_timeframe = True

    def update_position_size_tooltip(self, method_text):
        tooltips = {
            PositionSizingMethod.CONTRACT_SIZE.value: "Number of contracts per trade",
            PositionSizingMethod.EQUITY_PERCENT.value: "Percentage of current equity to risk per trade",
            PositionSizingMethod.SHARES.value: "Number of shares per trade",
            PositionSizingMethod.DOLLAR_AMOUNT.value: "Fixed dollar amount per trade"
        }
        self.position_size.setToolTip(tooltips.get(method_text, ""))

    def handle_header_click(self, section, table):
        """Handle sorting when a header is clicked."""
        if table not in self.sort_order_state:
            self.sort_order_state[table] = {}
        
        # Toggle sort order
        current_order = self.sort_order_state[table].get(section, Qt.SortOrder.AscendingOrder)
        new_order = Qt.SortOrder.DescendingOrder if current_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        
        # Sort the table
        table.sortItems(section, new_order)
        
        # Update the sort order state
        self.sort_order_state[table][section] = new_order

    def show_strategy_menu(self):
        """Show the strategy selection menu"""
        menu = PersistentMenu(self)
        
        # Add "Select All" and "Deselect All" options
        select_all = menu.addAction("Select All")
        deselect_all = menu.addAction("Deselect All")
        menu.addSeparator()
        
        # Add checkable actions for each strategy
        strategy_actions = {}
        for strategy_name, checkbox in self.strategy_checkboxes.items():
            action = menu.addAction(strategy_name)
            action.setCheckable(True)
            action.setChecked(checkbox.isChecked())
            strategy_actions[action] = strategy_name
        
        # Connect actions to handlers
        select_all.triggered.connect(lambda: self.handle_select_all(True, strategy_actions))
        deselect_all.triggered.connect(lambda: self.handle_select_all(False, strategy_actions))
        
        for action, strategy_name in strategy_actions.items():
            action.triggered.connect(lambda checked, s=strategy_name: self.handle_strategy_selection(s, checked))
        
        # Show menu under the button
        menu.exec(self.strategy_dropdown.mapToGlobal(self.strategy_dropdown.rect().bottomLeft()))

    def handle_select_all(self, select: bool, strategy_actions: dict):
        """Handle Select All / Deselect All actions"""
        for action in strategy_actions:
            action.setChecked(select)
            self.strategy_checkboxes[strategy_actions[action]].setChecked(select)
        self.update_strategy_count()

    def handle_strategy_selection(self, strategy_name: str, checked: bool):
        """Handle individual strategy selection"""
        self.strategy_checkboxes[strategy_name].setChecked(checked)
        self.update_strategy_count()

    def update_strategy_count(self):
        """Update the strategy count in the button text"""
        selected_count = sum(1 for checkbox in self.strategy_checkboxes.values() if checkbox.isChecked())
        total_count = len(self.strategy_checkboxes)
        self.strategy_dropdown.setText(f"Strategies ({selected_count}/{total_count}) ▼")

    def update_symbol_history(self, stock_symbols: List[str], crypto_symbols: List[str]):
        """Update symbol history after successful backtest"""
        if stock_symbols:
            self.symbol_manager.add_stock_symbols(stock_symbols)
        if crypto_symbols:
            self.symbol_manager.add_crypto_symbols(crypto_symbols)

    def show_symbol_menu(self, symbol_type: str):
        """Show the symbol selection menu"""
        menu = PersistentMenu(self)
        
        # Add "Select All" and "Deselect All" options
        select_all = menu.addAction("Select All")
        deselect_all = menu.addAction("Deselect All")
        menu.addSeparator()
        
        # Get symbols based on type
        symbols = (self.symbol_manager.get_stock_symbols() 
                  if symbol_type == "stock" 
                  else self.symbol_manager.get_crypto_symbols())
        
        # Create checkable actions for each symbol
        symbol_actions = {}
        if symbols:
            current_symbols = (self.stock_symbols.text().split(',') 
                             if symbol_type == "stock" 
                             else self.crypto_symbols.text().split(','))
            current_symbols = [s.strip().upper() for s in current_symbols if s.strip()]
            
            for symbol in symbols:
                action = menu.addAction(symbol)
                action.setCheckable(True)
                action.setChecked(symbol in current_symbols)
                symbol_actions[action] = symbol
        else:
            # Show placeholder text if no symbols
            no_symbols = menu.addAction("No recent symbols")
            no_symbols.setEnabled(False)
        
        # Connect actions to handlers
        select_all.triggered.connect(
            lambda: self.handle_select_all_symbols(True, symbol_actions, symbol_type))
        deselect_all.triggered.connect(
            lambda: self.handle_select_all_symbols(False, symbol_actions, symbol_type))
        
        for action, symbol in symbol_actions.items():
            action.triggered.connect(
                lambda checked, s=symbol, t=symbol_type: 
                self.handle_symbol_selection(s, t, checked))
        
        # Show menu under the appropriate dropdown button
        button = self.sender()
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def handle_select_all_symbols(self, select: bool, symbol_actions: dict, symbol_type: str):
        """Handle Select All / Deselect All actions for symbols"""
        symbols = []
        for action in symbol_actions:
            action.setChecked(select)
            if select:
                symbols.append(symbol_actions[action])
        
        # Update the appropriate line edit
        line_edit = self.stock_symbols if symbol_type == "stock" else self.crypto_symbols
        line_edit.setText(', '.join(symbols))

    def handle_symbol_selection(self, symbol: str, symbol_type: str, checked: bool):
        """Handle individual symbol selection"""
        line_edit = self.stock_symbols if symbol_type == "stock" else self.crypto_symbols
        current_text = line_edit.text().strip()
        symbols = [s.strip() for s in current_text.split(',') if s.strip()]
        
        if checked and symbol not in symbols:
            symbols.append(symbol)
        elif not checked and symbol in symbols:
            symbols.remove(symbol)
            
        line_edit.setText(', '.join(symbols))

    def generate_detailed_report(self, aggregated_results):
        report_data = {
            "Report Generated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Strategies": {}
        }

        for strategy_name, results in aggregated_results.items():
            strategy_instances = results.get('strategy_instances', [])
            strategy_instance = strategy_instances[0] if strategy_instances else None

            strategy_report = {
                "Strategy Overview": {
                    "Objective": getattr(strategy_instance, 'objective', 'Not specified'),
                    "Type of Strategy": getattr(strategy_instance, 'strategy_type', 'Not specified'),
                    "Market Context": getattr(strategy_instance, 'market_context', 'Not specified'),
                    "Time Horizon": getattr(strategy_instance, 'time_horizon', 'Not specified'),
                    "Assumptions": getattr(strategy_instance, 'assumptions', 'Not specified')
                },
                "Performance Metrics": {
                    "Return Metrics": {
                        "Net Profit": results.get('net_profit', 0),
                        "Total Return %": results.get('total_return', 0),
                        "Annualized Return %": results.get('annualized_return', 0)
                    },
                    "Risk-Adjusted Return": {
                        "Sharpe Ratio": results.get('sharpe_ratio', 0),
                        "Sortino Ratio": results.get('sortino_ratio', 0)
                    },
                    "Drawdown Metrics": {
                        "Maximum Drawdown %": results.get('max_drawdown', 0),
                        "Average Drawdown %": results.get('avg_drawdown', 0)
                    }
                },
                "Risk Analysis": {
                    "Volatility %": results.get('volatility', 0),
                    "Beta": results.get('beta', 0)
                }
            }

            # Add Trade Statistics
            strategy_report["Trade Statistics"] = {
                "Total Trades": results.get('total_trades', 0),
                "Winning Trades": results.get('winning_trades', 0),
                "Losing Trades": results.get('total_trades', 0) - results.get('winning_trades', 0),
                "Win Rate %": results.get('win_rate', 0),
                "Average Trade Duration (days)": results.get('avg_trade_duration', 0)
            }

            # Add Risk Management details
            if strategy_instance:
                strategy_report["Risk Management Framework"] = {
                    "Position Sizing Method": str(getattr(strategy_instance, 'position_sizing_method', 'Not specified')),
                    "Position Size Value": getattr(strategy_instance, 'position_size_value', 'Not specified')
                }
            else:
                strategy_report["Risk Management Framework"] = {
                    "Position Sizing Method": "Not Available",
                    "Position Size Value": "Not Available"
                }

            # Add Backtest Analysis
            strategy_report["Backtest Analysis"] = {
                "Data Quality": {
                    "Number of Symbols": results.get('total_symbols', 0),
                    "Symbols Tested": ", ".join(results.get('symbols', []))
                },
                "Backtest Settings": {
                    "Initial Capital": self.initial_capital.value(),
                    "Date Range": f"{self.start_date.date().toPyDate()} to {self.end_date.date().toPyDate()}",
                    "Timeframe": self.timeframe_selection.currentText()
                }
            }

            report_data["Strategies"][strategy_name] = strategy_report

        # Save the report to a JSON file
        report_file = "backtest_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=4, default=str)

        QMessageBox.information(self, "Report Generated", f"Detailed report saved to {report_file}")

class TradeDetailsDialog(QDialog):
    def __init__(self, trades, price_data):
        super().__init__()
        self.setWindowTitle("Trade Details")
        self.setGeometry(100, 100, 1200, 800)  # Made window larger to accommodate chart
        
        # Create main layout
        main_layout = QHBoxLayout()
        
        # Create splitter for resizable sections
        splitter = QSplitter()
        
        # Left side - Trade Details Table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        # Create and setup table
        trade_keys = ['entry_date', 'entry_price', 'position', 'exit_date', 'exit_price', 'profit']
        self.table = QTableWidget()
        self.table.setRowCount(len(trades))
        self.table.setColumnCount(len(trade_keys))
        self.table.setHorizontalHeaderLabels(trade_keys)
        
        for row, trade in enumerate(trades):
            for col, key in enumerate(trade_keys):
                self.table.setItem(row, col, QTableWidgetItem(str(trade.get(key, 'N/A'))))
        
        table_layout.addWidget(self.table)
        
        # Right side - Chart
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        # Create the figure and canvas for matplotlib
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        # Add widgets to splitter
        splitter.addWidget(table_widget)
        splitter.addWidget(chart_widget)
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
        # Plot the data
        self.plot_trades(price_data, trades)
        
    def plot_trades(self, price_data, trades):
        # Clear the figure
        self.figure.clear()
        
        # Create subplot
        ax = self.figure.add_subplot(111)
        
        # Plot price data
        ax.plot(price_data.index, price_data['Close'], label='Price', color='blue', alpha=0.6)
        
        # Plot entry points
        entry_dates = [trade['entry_date'] for trade in trades]
        entry_prices = [trade['entry_price'] for trade in trades]
        ax.scatter(entry_dates, entry_prices, color='green', marker='^', 
                  label='Entry', s=100)
        
        # Plot exit points
        exit_dates = [trade['exit_date'] for trade in trades]
        exit_prices = [trade['exit_price'] for trade in trades]
        ax.scatter(exit_dates, exit_prices, color='red', marker='v', 
                  label='Exit', s=100)
        
        # Customize the plot
        ax.set_title('Price Movement and Trades')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.grid(True)
        ax.legend()
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45)
        
        # Adjust layout to prevent label cutoff
        self.figure.tight_layout()
        
        # Refresh canvas
        self.canvas.draw() 