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
        # ADVANCED REACTIVE AI LOGIC
        # The AI now checks its previous quarter's sales to make decisions.
        # Total market is 2,000 consumers.
        
        if self.strategy == "Cost Leadership":
            if self.sales < 400:  # Losing market share? Panic and drop price.
                self.price = max(20.5, self.price - 0.5)
            elif self.sales > 800: # Monopoly? Raise prices to gouge consumers.
                self.price += 0.5
                
        elif self.strategy == "Differentiation":
            if self.sales < 200: # Too expensive for the market? Drop premium price slightly.
                self.price = max(30.0, self.price - 1.0)
            else: # Selling well? Keep increasing quality and price.
                self.differentiation_cost = min(25.0, self.differentiation_cost + 0.5)
                self.price = 20.0 + self.differentiation_cost + 15.0 
                
        elif self.strategy == "Innovation":
            if self.sales < 200: # Losing volume? Make the product more accessible.
                self.price = max(25.0, self.price - 0.5)
            self.innovation_spend += 50.0 # Always keep R&D ticking up
            
        elif self.strategy == "Market Expansion":
            if self.sales < 500: # Not enough reach? Buy more ads and cut price.
                self.ad_spend += 100.0
                self.price = max(21.0, self.price - 0.5)
            else: # Captured the market? Stop dropping price.
                self.price += 0.5
