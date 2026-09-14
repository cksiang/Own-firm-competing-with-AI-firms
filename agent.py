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
        # --- 1. ECOSYSTEM INTELLIGENCE (THE RADAR) ---
        all_firms = getattr(self.model, 'firm_agents', [])
        if not all_firms:
            return 
            
        total_market_sales = sum(getattr(a, 'sales', 0) for a in all_firms)
        # Default to a 20% assumed share on Turn 1 before sales happen
        my_market_share = (self.sales / total_market_sales) if total_market_sales > 0 else 0.20 
        
        # Spy on competitors
        competitors = [a for a in all_firms if getattr(a, 'unique_id', None) != getattr(self, 'unique_id', None)]
        comp_prices = [getattr(a, 'price', 40.0) for a in competitors]
        min_comp_price = min(comp_prices) if comp_prices else 40.0
        avg_comp_price = sum(comp_prices) / len(comp_prices) if comp_prices else 40.0
        
        comp_ads = [getattr(a, 'target_ads', getattr(a, 'ad_spend', 0.0)) for a in competitors]
        max_comp_ads = max(comp_ads) if comp_ads else 0.0


        # --- 2. SUPER-INTELLIGENT REACTIVE STRATEGIES ---
        
        if self.strategy == "Cost Leadership":
            # Goal: ALWAYS be the cheapest option on the board.
            if my_market_share < 0.25 or self.price >= min_comp_price:
                # Undercut the absolute lowest competitor in the market
                self.price = max(20.50, min_comp_price - 0.50)
            elif my_market_share > 0.35 and self.price < (min_comp_price - 1.0):
                # If dominating, safely raise prices to take profits, remaining just slightly cheaper
                self.price = min_comp_price - 0.25

                
        elif self.strategy == "Differentiation":
            # Goal: Protect the premium brand image and quality gap.
            if my_market_share < 0.15:
                # If losing share, actively boost physical quality (up to +$25)
                self.differentiation_cost = min(25.0, self.differentiation_cost + 1.0)
                # Ensure price justifies the quality, but peg it to the market average to remain somewhat competitive
                self.price = max(avg_comp_price + 5.0, 20.0 + self.differentiation_cost + 10.0)
            else:
                # If maintaining healthy premium share, slowly raise prices to test elasticity
                self.price += 0.50

                
        elif self.strategy == "Innovation":
            # Goal: Leverage massive R&D, but don't spend into bankruptcy
            if my_market_share < 0.20:
                self.innovation_spend += 150.0
                self.differentiation_cost = min(15.0, self.differentiation_cost + 0.5)
                self.price = max(25.0, min(self.price - 1.0, avg_comp_price + 2.0))
            else:
                # Cap R&D spend at 30% of previous revenue to ensure profitability
                max_safe_rd = self.revenue * 0.30 if self.revenue > 0 else 500.0
                self.innovation_spend = min(self.innovation_spend + 50.0, max_safe_rd)
                self.price += 1.0
                
                
        elif self.strategy == "Market Expansion":
            # Goal: Win the marketing war by outspending everyone else in the ecosystem.
            if my_market_share < 0.25:
                # Must out-advertise the highest spender in the market
                self.ad_spend = max_comp_ads + 200.0
                # Peg price slightly below the market average to maximize ad conversion
                self.price = max(21.0, avg_comp_price - 1.0)
            elif my_market_share > 0.40:
                # Captured a massive monopoly? Slash ad spend to save cash and slowly raise price
                self.ad_spend = max(200.0, self.ad_spend - 100.0)
                self.price += 0.50
