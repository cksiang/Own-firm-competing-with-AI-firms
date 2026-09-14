import mesa
import random
from agent import FirmAgent
from agent_execution import batch_consumer_choice

class HumanFirm(mesa.Agent):
    def __init__(self, *args, **kwargs):
        unique_id = kwargs.get('unique_id', None)
        model = kwargs.get('model', None)

        if args:
            if len(args) >= 2:
                unique_id, model = args[0], args[1]
            elif len(args) == 1:
                if isinstance(args[0], mesa.Model):
                    model = args[0]
                else:
                    unique_id = args[0]

        try:
            super().__init__(unique_id, model)
        except TypeError:
            super().__init__(model)
            
        if unique_id is not None:
            self.unique_id = unique_id

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
        
        self.cash -= (self.target_ads + self.target_inn)
        
        self.ad_queue.append(self.target_ads)
        self.inn_queue.append(self.target_inn)
        
        self.ad_spend = self.ad_queue.pop(0)
        self.innovation_spend = self.inn_queue.pop(0)


class InteractiveMarketModel(mesa.Model):
    def __init__(self, num_ai_firms=4, num_consumers=2000):
        try:
            super().__init__()
        except Exception:
            pass
            
        self.num_consumers = num_consumers
        self.steps = 0 
        self.firm_agents = [] 
        
        self.schedule = mesa.time.RandomActivation(self) if hasattr(mesa, 'time') and hasattr(mesa.time, 'RandomActivation') else None
        
        strategies = ["Cost Leadership", "Differentiation", "Innovation", "Market Expansion"]
        for i in range(num_ai_firms):
            strat = strategies[i % len(strategies)]
            
            # THE FIX: Explicitly handle the 2 vs 3 positional argument limit
            try:
                # Try Mesa 2.x standard format
                a = FirmAgent(i, self, strategy=strat)
            except TypeError:
                # If it rejects 4 arguments, use the Mesa 3.0+ format (model, strategy)
                a = FirmAgent(self, strategy=strat)
                a.unique_id = i
                
            self.firm_agents.append(a)
            
            if self.schedule:
                self.schedule.add(a)
            elif hasattr(self, 'agents') and hasattr(self.agents, 'add'):
                try:
                    self.agents.add(a)
                except Exception:
                    pass
                
        human = HumanFirm(num_ai_firms, self)
        self.human_firm = human
        self.firm_agents.append(human)
        
        if self.schedule:
            self.schedule.add(human)
        elif hasattr(self, 'agents') and hasattr(self.agents, 'add'):
            try:
                self.agents.add(human)
            except Exception:
                pass
            
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
        
        for a in self.firm_agents:
            if hasattr(a, 'step'):
                a.step()
                
        if self.schedule:
            if hasattr(self.schedule, 'steps'):
                self.schedule.steps += 1
            if hasattr(self.schedule, 'time'):
                self.schedule.time += 1
        
        firm_states = [{
            'id': a.unique_id, 
            'price': getattr(a, 'price', 40.0), 
            'strategy': getattr(a, 'strategy', ''), 
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
            a.revenue = a.sales * getattr(a, 'price', 40.0)
            
            base_cost = 20.0 
            diff_cost = getattr(a, 'differentiation_cost', 0.0)
            fixed_costs = getattr(a, 'target_ads', getattr(a, 'ad_spend', 0.0)) + getattr(a, 'target_inn', getattr(a, 'innovation_spend', 0.0))
            
            a.profit = a.revenue - (a.sales * (base_cost + diff_cost)) - fixed_costs
            
            if hasattr(a, 'cash'):
                a.cash += (a.revenue - (a.sales * (base_cost + diff_cost)))
                
        self.datacollector.collect(self)
