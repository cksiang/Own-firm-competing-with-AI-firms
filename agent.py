import mesa

class FirmAgent(mesa.Agent):
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            super().__init__(args[0])
        elif len(args) >= 2:
            try:
                super().__init__(args[0], args[1])
            except TypeError:
                super().__init__(args[1])
        elif 'model' in kwargs:
            super().__init__(kwargs['model'])
            
        self.strategy = kwargs.get('strategy', "Cost Leadership")
        if len(args) >= 3:
            self.strategy = args[2]

        self.price = 40.0
        self.sales = 0
        self.revenue = 0
        self.profit = 0
        self.ad_spend = 0.0
        self.innovation_spend = 0.0
        self.differentiation_cost = 0.0
        
        # Base Starting Positions
        if self.strategy == "Cost Leadership":
            self.price = 24.0
        elif self.strategy == "Differentiation":
            self.price = 44.0
            self.differentiation_cost = 5.0
        elif self.strategy == "Innovation":
            self.price = 45.0
            self.innovation_spend = 500.0
        elif self.strategy == "Market Expansion":
            self.price = 24.0
            self.ad_spend = 500.0

    def step(self):
        # RESTORED: Aggressive AI Competition Logic
        if self.strategy == "Cost Leadership":
            # Ruthlessly cut prices over time to steal volume
            self.price = max(21.0, self.price - 0.5)
        elif self.strategy == "Differentiation":
            # Continuously improve quality to justify premium pricing
            self.differentiation_cost = min(20.0, self.differentiation_cost + 1.0)
            self.price = 20.0 + self.differentiation_cost + 15.0 
        elif self.strategy == "Innovation":
            # Compound R&D spending to capture the inelastic market
            self.innovation_spend += 100.0
        elif self.strategy == "Market Expansion":
            # Flood the market with ads while slowly dropping price
            self.ad_spend += 100.0
            self.price = max(22.0, self.price - 0.25)
