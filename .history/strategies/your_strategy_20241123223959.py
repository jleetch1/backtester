class YourStrategy(BaseStrategy):
    def __init__(self, initial_capital: float):
        super().__init__(initial_capital)
        self.objective = "Maximize returns through momentum trading"
        self.strategy_type = "Momentum"
        self.market_context = "Equities"
        self.time_horizon = "Swing Trading"
        self.assumptions = "Assumes trending markets"

    # ... existing methods ... 