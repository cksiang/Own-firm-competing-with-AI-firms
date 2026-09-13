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
        
        self.cash = 100000.0  
        self.is_bankrupt = False
        
        self.ad_queue = [0.0, 0.0, 0.0]
        self.inn_queue = [0.0, 0.0, 0.0]
        
        self.sales = 0
        self.revenue = 0
        self.profit = 0
        self.ad_spend = 0.0
        self.innovation_spend = 0.0
        self.differentiation_cost = 0.0

    def step(self):
        if self.cash <= 0:
            self.is_bankrupt = True
            return
            
        self.price = self.target_price
        self.differentiation_cost = self.target_diff
        
        # Physically deduct the cash here
        self.cash -= (self.target_ads + self.target_inn)
        
        self.ad_queue.append(self.target_ads)
        self.inn_queue.append(self.target_inn)
        
        self.ad_spend = self.ad_queue.pop(0)
        self.innovation_spend = self.inn_queue.pop(0)


class InteractiveMarketModel(mesa.Model):
    def __init__(self, num_ai_firms=4, num_consumers=2000):
        super().__init__()
        self.num_consumers = num_consumers
        self.steps = 0 
        
        # ---> THE FIX: Direct Object References <---
        self.firm_agents = [] 
        
        # Keep schedule strictly for the DataCollector's background requirements
        self.schedule = mesa.time.RandomActivation(self) if hasattr(mesa.time, 'RandomActivation') else None
        
        strategies = ["Cost Leadership", "Differentiation", "Innovation", "Market Expansion"]
        for i in range(num_ai_firms):
            a = FirmAgent(i, self, strategies[i % len(strategies)])
            self.firm_agents.append(a)
            if self.schedule:
                self.schedule.add(a)
            else:
                self.agents.add(a)
                
        # Hardwire the human firm so app.py can grab it flawlessly
        self.human_firm = HumanFirm(num_ai_firms, self)
        self.firm_agents.append(self.human_firm)
        
        if self.schedule:
            self.schedule.add(self.human_firm)
        else:
            self.agents.add(self.human_firm)
            
        self.consumers = [{'id': i, 'price_sensitivity': random.uniform(0.5, 1.5)} for i in range(num_consumers)]
        
        self.datacollector = mesa.DataCollector(
            agent_reporters={
                "Strategy": "strategy",
                "Price": "price",
                "Sales": "sales",
                "Profit": "profit"
            }
        )
        
    def step(self):
        self.steps += 1 
        
        # ---> THE FIX: Explicitly force the agents to act <---
        for a in self.firm_agents:
            if hasattr(a, 'step'):
                a.step()
                
        # Advance Mesa's background clock safely
        if self.schedule:
            self.schedule.steps += 1
            self.schedule.time += 1
        
        firm_states = [{
            'id': a.unique_id, 'price': a.price, 'strategy': a.strategy, 
            'ad_spend': getattr(a, 'ad_spend', 0.0),
            'innovation_spend': getattr(a, 'innovation_spend', 0.0),
            'differentiation_cost': getattr(a, 'differentiation_cost', 0.0)
        } for a in self.firm_agents]
        
        all_choices = batch_consumer_choice(self.consumers, firm_states)
        
        from collections import Counter
        sales_counts = Counter([firm_id for cons_id, firm_id in all_choices])
        
        for a in self.firm_agents:
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
            
            if hasattr(a, 'cash'):
                a.cash += (a.revenue - (a.sales * (base_cost + diff_cost)))
                
        self.datacollector.collect(self)
