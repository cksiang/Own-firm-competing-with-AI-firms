import ray
import random

@ray.remote
def batch_consumer_choice(consumers, firm_states):
    choices = []
    
    for cons in consumers:
        base_wtp = random.gauss(65.0, 15.0) 
        sensitivity = cons.get('price_sensitivity', 1.0)
        
        best_firm = 'NO_PURCHASE'
        max_surplus = 0.0 
        
        for firm in firm_states:
            perceived_value = base_wtp
            
            # AI Firm static advantages
            if firm['strategy'] in ["Innovation", "Differentiation"]:
                perceived_value *= 1.2 
                
            # HUMAN STRATEGY 1: Innovation / R&D (Diminishing Multiplier)
            if firm.get('innovation_spend', 0) > 0:
                inn_multiplier = 1.0 + (firm['innovation_spend'] / (firm['innovation_spend'] + 1000.0)) * 0.25
                perceived_value *= inn_multiplier
                
            # HUMAN STRATEGY 2: Differentiation / Quality (Linear Value Addition)
            # Every extra $1 spent on unit quality adds $1.50 to perceived value
            if firm.get('differentiation_cost', 0) > 0:
                perceived_value += (firm['differentiation_cost'] * 1.5)
                
            # HUMAN STRATEGY 3: Advertising (Brand Prestige Multiplier)
            if firm.get('ad_spend', 0) > 0:
                ad_boost_multiplier = 1.0 + (firm['ad_spend'] / (firm['ad_spend'] + 500.0))
                perceived_value *= ad_boost_multiplier
            
            # Subjective Brand Preference (Noise)
            subjective_bonus = random.gauss(0, 8.0) 
            
            # Calculate final Surplus
            surplus = (perceived_value + subjective_bonus) - (firm['price'] * sensitivity)
            
            if surplus > max_surplus:
                max_surplus = surplus
                best_firm = firm['id']
                
        if best_firm != 'NO_PURCHASE':
            choices.append((cons['id'], best_firm))
            
    return choices