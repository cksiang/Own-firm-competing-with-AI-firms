import mesa

class FirmAgent(mesa.Agent):
    def __init__(self, *args, **kwargs):
        # 1. Handle Mesa 2.x (unique_id, model) vs Mesa 3.x (model) differences
        if len(args) == 1:
            super().__init__(args[0])
        elif len(args) >= 2:
            try:
                super().__init__(args[0], args[1])
            except TypeError:
                super().__init__(args[1])
        elif 'model' in kwargs:
            super().__init__(kwargs['model'])
            
        # 2. Extract strategy safely
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
        
        # 3. Apply baseline presets
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
        pass
