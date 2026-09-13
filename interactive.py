import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Slider
import pandas as pd
import mesa
from collections import Counter


from agent import FirmAgent
from agent_execution import batch_consumer_choice

# --- 1. DEFINE THE HUMAN-CONTROLLED AGENT ---
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
        if self.cash <= 0:
            self.is_bankrupt = True
            return
            
        self.price = self.target_price
        self.differentiation_cost = self.target_diff
        
        # Deduct R&D and Ad spend from your bank account instantly
        self.cash -= (self.target_ads + self.target_inn)
        
        # Queue the investments for the future
        self.ad_queue.append(self.target_ads)
        self.inn_queue.append(self.target_inn)
        
        # Realize the investments you made 3 quarters ago
        self.ad_spend = self.ad_queue.pop(0)
        self.innovation_spend = self.inn_queue.pop(0)


# --- 2. THE MARKET MODEL ---
class InteractiveMarketModel(mesa.Model):
    def __init__(self, num_ai_firms=4, num_consumers=10000):
        super().__init__()
        self.num_consumers = num_consumers
        self.human_target_price = 40.0 
        self.human_target_ads = 0.0    
        self.human_target_inn = 0.0
        self.human_target_diff = 0.0
        
        self.human_firm = HumanFirm(self)
        
        strategies = ["Cost Leadership", "Innovation", "Differentiation", "Market Expansion"]
        for i in range(num_ai_firms):
            FirmAgent(self, strategy=strategies[i % len(strategies)])
            
        self.consumers = [{'id': f"cons_{j}", 'price_sensitivity': mesa.space.np.random.uniform(0.2, 0.9)}
                          for j in range(self.num_consumers)]

        self.datacollector = mesa.DataCollector(
            agenttype_reporters={
                FirmAgent: {"Strategy": "strategy", "Price": "price", "Sales": "sales", "Profit": "profit"},
                HumanFirm: {"Strategy": "strategy", "Price": "price", "Sales": "sales", "Profit": "profit"}
            }
        )

    def step(self):
        # 1. Grab active agents (safeguard for different Mesa versions)
        firm_agents = self.schedule.agents if hasattr(self, 'schedule') else self.agents
        
        firm_states = [{
            'id': a.unique_id, 'price': a.price, 'strategy': a.strategy, 
            'ad_spend': getattr(a, 'ad_spend', 0.0),
            'innovation_spend': getattr(a, 'innovation_spend', 0.0),
            'differentiation_cost': getattr(a, 'differentiation_cost', 0.0)
        } for a in firm_agents]
        
        # 2. Standard Python Execution
        all_choices = batch_consumer_choice(self.consumers, firm_states)
        
        from collections import Counter
        sales_counts = Counter([firm_id for cons_id, firm_id in all_choices])
        
        # 3. Calculate Sales, Revenue, and Profit
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
            
            # Update the graph metric
            a.profit = a.revenue - (a.sales * (base_cost + diff_cost)) - fixed_costs
            
            # Deposit the gross margin into the Human firm's bank account
            if hasattr(a, 'cash'):
                a.cash += (a.revenue - (a.sales * (base_cost + diff_cost)))
                
        # 4. Advance the Simulation Clock (Crucial for graphs!)
        if hasattr(self, 'schedule'):
            self.schedule.step() # Moves Step 1 -> 2 -> 3
        else:
            self.agents.shuffle_do("step")
            self.steps += 1      # Moves Step 1 -> 2 -> 3
            
        # 5. Collect the new step data
        self.datacollector.collect(self)


if __name__ == "__main__":
    sim_model = InteractiveMarketModel(num_ai_firms=4, num_consumers=10000)
    
    # --- 3. DASHBOARD UI SETUP ---
    fig, (ax_share, ax_profit) = plt.subplots(1, 2, figsize=(14, 8))
    fig.suptitle("Human vs AI: Full Strategy Simulation", fontsize=16, fontweight='bold')
    plt.subplots_adjust(bottom=0.40) # Make room for 4 sliders
    
    # Sliders UI
    ax_price_slider = plt.axes([0.2, 0.25, 0.6, 0.03])
    price_slider = Slider(ax_price_slider, 'Price ($)', 10.0, 100.0, valinit=40.0, valstep=1.0)
    
    ax_ads_slider = plt.axes([0.2, 0.18, 0.6, 0.03])
    ads_slider = Slider(ax_ads_slider, 'Ad Spend ($/turn)', 0.0, 5000.0, valinit=0.0, valstep=100.0)
    
    ax_inn_slider = plt.axes([0.2, 0.11, 0.6, 0.03])
    inn_slider = Slider(ax_inn_slider, 'Innovation R&D ($/turn)', 0.0, 5000.0, valinit=0.0, valstep=100.0)
    
    ax_diff_slider = plt.axes([0.2, 0.04, 0.6, 0.03])
    diff_slider = Slider(ax_diff_slider, 'Quality (+$ Cost/Unit)', 0.0, 30.0, valinit=0.0, valstep=1.0)
    
    def update_human_strategy(val):
        sim_model.human_target_price = price_slider.val
        sim_model.human_target_ads = ads_slider.val
        sim_model.human_target_inn = inn_slider.val
        sim_model.human_target_diff = diff_slider.val
        
    price_slider.on_changed(update_human_strategy)
    ads_slider.on_changed(update_human_strategy)
    inn_slider.on_changed(update_human_strategy)
    diff_slider.on_changed(update_human_strategy)
    
    color_map = {'My Company (Human)': 'blue', 'Cost Leadership': 'red', 'Innovation': 'green', 'Differentiation': 'orange', 'Market Expansion': 'purple'}

    # --- 4. ANIMATION LOOP ---
    def update_dashboard(frame):
        sim_model.step()
        
        ai_df = sim_model.datacollector.get_agenttype_vars_dataframe(FirmAgent)
        human_df = sim_model.datacollector.get_agenttype_vars_dataframe(HumanFirm)
        firm_df = pd.concat([ai_df, human_df])
        
        if firm_df.empty: return
        
        df_reset = firm_df.reset_index()
        sales_data = df_reset.pivot(index='Step', columns='Strategy', values='Sales').fillna(0)
        profit_data = df_reset.pivot(index='Step', columns='Strategy', values='Profit').fillna(0)
        
        market_share = sales_data.div(sales_data.sum(axis=1), axis=0) * 100
        
        ax_share.clear()
        ax_profit.clear()
        
        plot_colors = [color_map.get(col, 'gray') for col in market_share.columns]
        
        if not market_share.empty:
            market_share.plot(ax=ax_share, kind='area', color=plot_colors, alpha=0.7, legend=False)
        ax_share.set_title("Live Market Share")
        ax_share.set_ylabel("Share (%)")
        
        profit_data.plot(ax=ax_profit, color=plot_colors, linewidth=2)
        ax_profit.set_title("Live Profitability")
        ax_profit.set_ylabel("Total Profit ($)")
        ax_profit.legend(title="Firms", loc='upper left', fontsize='small')

    ani = animation.FuncAnimation(fig, update_dashboard, interval=500, cache_frame_data=False)
    plt.show()
