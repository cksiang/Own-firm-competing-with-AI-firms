import mesa

class FirmAgent(mesa.Agent):
    def __init__(self, *args, **kwargs):
        # Extract arguments dynamically regardless of caller signature
        unique_id = kwargs.get('unique_id', None)
        model = kwargs.get('model', None)
        strategy = kwargs.get('strategy', "Cost Leadership")

        if args:
            if len(args) == 3:
                unique_id, model, strategy = args[0], args[1], args[2]
            elif len(args) == 2:
                if isinstance(args[0], mesa.Model):
                    model, strategy = args[0], args[1]
                else:
                    unique_id, model = args[0], args[1]
            elif len(args) == 1:
                model = args[0]

        # Polyfill Mesa 2.x vs 3.x Agent init
        try:
            super().__init__(unique_id, model)
        except TypeError:
            super().__init__(model)
            
        if unique_id is not None:
            self.unique_id = unique_id
            
        self.strategy = strategy
        self.price = 40.0
        self.sales = 0
        self.revenue = 0
        self.profit = 0
        self.ad_spend = 0.0
        self.innovation_spend = 0.0
        self.differentiation_cost = 0.0
        
        # Presets
        if strategy == "Cost Leadership":
            self.price = 24.0
        elif strategy == "Differentiation":
            self.price = 44.0
            self.differentiation_cost = 5.0
        elif strategy == "Innovation":
            self.price = 45.0
            self.innovation_spend = 500.0
        elif strategy == "Market Expansion":
            self.price = 24.0
            self.ad_spend = 500.0

    def step(self):
        pass
