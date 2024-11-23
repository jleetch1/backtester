import json
import os
from typing import List, Set

class SymbolManager:
    def __init__(self, storage_file: str = "symbol_history.json"):
        self.storage_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), storage_file)
        self.symbols = self._load_symbols()
    
    def _load_symbols(self) -> dict:
        """Load symbols from storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"stocks": [], "crypto": []}
        return {"stocks": [], "crypto": []}
    
    def _save_symbols(self):
        """Save symbols to storage file"""
        with open(self.storage_file, 'w') as f:
            json.dump(self.symbols, f)
    
    def add_stock_symbols(self, symbols: List[str]):
        """Add stock symbols to history"""
        current_set = set(self.symbols["stocks"])
        for symbol in symbols:
            if symbol.strip():
                current_set.add(symbol.strip().upper())
        self.symbols["stocks"] = list(current_set)
        self._save_symbols()
    
    def add_crypto_symbols(self, symbols: List[str]):
        """Add crypto symbols to history"""
        current_set = set(self.symbols["crypto"])
        for symbol in symbols:
            if symbol.strip():
                current_set.add(symbol.strip().upper())
        self.symbols["crypto"] = list(current_set)
        self._save_symbols()
    
    def get_stock_symbols(self) -> List[str]:
        """Get list of stored stock symbols"""
        return sorted(self.symbols["stocks"])
    
    def get_crypto_symbols(self) -> List[str]:
        """Get list of stored crypto symbols"""
        return sorted(self.symbols["crypto"]) 