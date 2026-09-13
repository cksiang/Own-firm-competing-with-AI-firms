import mesa
import random

class FirmAgent(mesa.Agent):
    """Fully realized AI Competitor with economies of scale and dynamic ad budgets."""
    def __init__(self, model, strategy="Innovation"):
        super().__init__(model)
        self.strategy = strategy
        self.revenue = 0.0
        self.profit = 0.0
        self.sales = 0
        self.ad_spend = 0.0
        
        # Corporate Archetypes (Starting Price, Base Cost, Ad Reinvestment Rate)
        if self.strategy == "Cost Leadership":
            self.price, self.base_cost = 20.0, 15.0
            self.ad_reinvestment_rate = 0.00  # Rely purely on cheap prices
        elif self.strategy == "Differentiation":
            self.price, self.base_cost = 40.0, 20.0
            self.ad_reinvestment_rate = 0.15  # Spends 15% of revenue on Ads
        elif self.strategy == "Innovation":
            self.price, self.base_cost = 45.0, 25.0
            self.ad_reinvestment_rate = 0.05  # Word-of-mouth + tech appeal
        else: # Market Expansion (The Disruptor)
            self.price, self.base_cost = 25.0, 18.0
            self.ad_reinvestment_rate = 0.20  # Burns cash to buy market share

        # Q-Learning setup for pricing strategy
        self.q_table = {}
        self.actions = [-1.0, 0.0, 1.0] # Price adjustments
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.2
        self.last_state = "stable_market"
        self.last_action = 0.0

    def step(self):

        # ---> AI PANIC STATE <---
        # If an AI firm drops below 100 sales (5% market share), it enters survival mode.
        if hasattr(self, 'sales') and self.sales < 100:
            self.price = 22.0  # Slash prices drastically to just above base cost
            self.ad_spend += 500.0  # Dump remaining capital into aggressive marketing
            # Skip normal Q-learning this turn to execute emergency protocol
            return
        # 1. Economies of Scale: Selling more units decreases the base manufacturing cost
        # Max discount is 20% off base cost if they capture the whole market
        scale_discount = min(0.20, self.sales / 10000.0)
        current_unit_cost = self.base_cost * (1.0 - scale_discount)
        
        # 2. Financials
        self.profit = self.revenue - (current_unit_cost * self.sales) - self.ad_spend
        
        # 3. Dynamic Budgeting: Reinvest revenue into next turn's Ad Spend
        self.ad_spend = self.revenue * self.ad_reinvestment_rate
        
        # 4. Q-Learning Price Adjustments
        current_state = "stable_market"
        
        if self.last_state is not None and self.last_action is not None:
            old_q = self.q_table.get(self.last_state, {}).get(self.last_action, 0.0)
            future_q = max(self.q_table.get(current_state, {a: 0.0 for a in self.actions}).values())
            new_q = old_q + self.learning_rate * (self.profit + self.discount_factor * future_q - old_q)
            
            if self.last_state not in self.q_table:
                self.q_table[self.last_state] = {a: 0.0 for a in self.actions}
            self.q_table[self.last_state][self.last_action] = new_q

        if current_state not in self.q_table:
            self.q_table[current_state] = {a: 0.0 for a in self.actions}
            
        if random.random() < self.exploration_rate:
            action = random.choice(self.actions)
        else:
            action = max(self.q_table[current_state], key=self.q_table[current_state].get)
            
        # Execute Action (Ensure they don't price below their dynamically lowered cost)
        self.price = max(current_unit_cost + 1.0, self.price + action)
        self.last_action = action
