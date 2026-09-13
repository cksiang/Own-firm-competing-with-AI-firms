import mesa
import random
from agent import FirmAgent
from agent_execution import batch_consumer_choice

class HumanFirm(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.strategy = "My Company (Human)"
        self.price = 40.0
        self.target_price = 40.0
        self.target_ads = 0.0
        self.target_inn = 0.0
        self.target_diff = 0.0
        
        # 1. HARD CASH CONSTRAINT
        self.cash = 100000.0  
        self.is_bankrupt = False
        
        # 2. STRATEGIC LAG (3-Quarter Delay)
        self.ad_queue = [0.0, 0.0, 0.0]
        self.inn_queue = [0.0, 0.0, 0.0]
        
        self.sales = 0
        self.revenue = 0
        self.profit = 0
        self.ad_spend = 0.0
        self.innovation_spend = 0.0
        self.differentiation_cost = 0.0

    def step(self):
        # Bankruptcy Check
        if self.cash <= 0:
            self.is_bankrupt = True
            return
            
        self.price = self.target_price
        self.differentiation_cost = self.target_diff
        
        # Deduct R&D and Ad spend instantly from the bank account
        self.cash -= (self.target_ads + self.target_inn)
        
        # Queue the investments for future quarters
        self.ad_queue.append(self.target_ads)
        self.inn_queue.append(self.target_inn)
        
        # Realize past investments
        self.ad_spend = self.ad_queue.pop(0)
        self.innovation_spend = self.inn_queue.pop(0)


class InteractiveMarketModel(mesa.Model):
    def __init__(self, num_ai_firms=4, num_consumers=2000):
        super().__init__()
        self.num_consumers = num_consumers
        
        # Compatibility handling for different Mesa versions
        self.schedule = mesa.time.RandomActivation(self) if hasattr(mesa.time, 'RandomActivation') else None
        
        # Initialize AI Firms
        strategies = ["Cost Leadership", "Differentiation", "Innovation", "Market Expansion"]
        for i in range(num_ai_firms):
            a = FirmAgent(i, self, strategies[i % len(strategies)])
            if self.schedule:
                self.schedule.add(a)
            else:
                self.agents.add(a)
                
        # Initialize Human Firm
        human = HumanFirm(num_ai_firms, self)
        if self.schedule:
            self.schedule.add(human)
        else:
            self.agents.add(human)
            
        # Initialize Synthetic Consumers
        self.consumers = [{'id': i, 'price_sensitivity': random.uniform(0.5, 1.5)} for i in range(num_consumers)]
        
        # Data Collection Setup
        self.datacollector = mesa.DataCollector(
            agent_reporters={
                "Strategy": "strategy",
                "Price": "price",
                "Sales": "sales",
                "Profit": "profit"
            }
        )
        
    def step(self):
        firm_agents = self.schedule.agents if hasattr(self, 'schedule') else self.agents
        
        firm_states = [{
            'id': a.unique_id, 'price': a.price, 'strategy': a.strategy, 
            'ad_spend': getattr(a, 'ad_spend', 0.0),
            'innovation_spend': getattr(a, 'innovation_spend', 0.0),
            'differentiation_cost': getattr(a, 'differentiation_cost', 0.0)
        } for a in firm_agents]
        
        # Process Consumer Choices
        all_choices = batch_consumer_choice(self.consumers, firm_states)
        
        from collections import Counter
        sales_counts = Counter([firm_id for cons_id, firm_id in all_choices])
        
        # Calculate Financials & Update Bank Accounts
        for a in firm_agents:
            if getattr(a, 'is_bankrupt', False):
                a.sales = 0
                a.revenue = 0
                a.profit = 0
                continue
                
            a.sales = sales_counts.get(a.unique_id, 0)
            a.revenue = a.sales * a.price
            
            base_cost = 20.0 
            diff_cost = getattr(a, 'differentiation_cost', 0.0)
            fixed_costs = getattr(a, 'target_ads', getattr(a, 'ad_spend', 0.0)) + getattr(a, 'target_inn', getattr(a, 'innovation_spend', 0.0))
            
            a.profit = a.revenue - (a.sales * (base_cost + diff_cost)) - fixed_costs
            
            # Replenish cash from gross margin sales
            if hasattr(a, 'cash'):
                a.cash += (a.revenue - (a.sales * (base_cost + diff_cost)))
                
        # Advance the simulation clock for all agents
        if hasattr(self, 'schedule'):
            self.schedule.step()
        else:
            self.agents.shuffle_do("step")
            
        # Log the quarter's data for the charts
        self.datacollector.collect(self)
