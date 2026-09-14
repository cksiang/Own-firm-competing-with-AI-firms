import mesa

class FirmAgent(mesa.Agent):
    def __init__(self, *args, **kwargs):
        # Keeps your stable initialization intact
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
        
        # Starting Positions
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
        # INTELLIGENT AGGRESSIVE LOGIC
        # Total market is 2,000 consumers. Fair share is 400 per firm.
        
        if self.strategy == "Cost Leadership":
            # Goal: Maximize volume at razor-thin margins
            if self.sales < 500:  
                # Losing share? Undercut aggressively, down to 50 cents profit.
                self.price = max(20.5, self.price - 0.50) 
            elif self.sales > 800: 
                # Monopolizing? Slowly raise price to take profits.
                self.price += 0.25 
                
        elif self.strategy == "Differentiation":
            # Goal: Premium quality, high margins
            if self.sales < 250: 
                # Losing share? Improve quality up to the $20 cap. If capped, drop the premium.
                if self.differentiation_cost < 20.0:
                    self.differentiation_cost += 1.0
                else:
                    self.price = max(35.0, self.price - 1.0)
            else: 
                # Selling well? Keep pushing the price up.
                self.price += 0.50
                
        elif self.strategy == "Innovation":
            # Goal: Win the inelastic market through compounding R&D and cutting-edge features
            if self.sales < 300: 
                # Losing loyalists? Boost R&D, improve physical quality, and slightly drop price.
                self.innovation_spend += 100.0 
                # R&D leads to better physical parts, increasing unit cost up to a +$15 cap
                self.differentiation_cost = min(15.0, self.differentiation_cost + 0.5)
                self.price = max(28.0, self.price - 0.50)
            else:
                # Dominating? Exploit brand loyalty with price hikes, but keep R&D ticking to stay ahead.
                self.innovation_spend += 50.0
                self.price += 1.0
            
        elif self.strategy == "Market Expansion":
            # Goal: Buy market share with massive ad budgets
            if self.sales < 600: 
                # Not enough volume? Flood the zone with ads and slash price.
                self.ad_spend += 200.0 
                self.price = max(21.0, self.price - 0.50)
            else:
                # Captured the market? Pull back ad spend to save cash and slowly raise price.
                self.ad_spend = max(500.0, self.ad_spend - 50.0) 
                self.price += 0.25
