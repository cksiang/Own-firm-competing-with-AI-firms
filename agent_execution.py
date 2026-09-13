import random

def batch_consumer_choice(consumers, firm_states):
    choices = []
    
    for cons in consumers:
        base_wtp = random.gauss(65.0, 15.0) 
        sensitivity = cons.get('price_sensitivity', 1.0)
        
        best_firm = 'NO_PURCHASE'
        max_surplus = 0.0 
        
        for firm in firm_states:
            perceived_value = base_wtp
            
            if firm['strategy'] in ["Innovation", "Differentiation"]:
                perceived_value *= 1.2 
                
            if firm.get('innovation_spend', 0) > 0:
                inn_multiplier = 1.0 + (firm['innovation_spend'] / (firm['innovation_spend'] + 1000.0)) * 0.25
                perceived_value *= inn_multiplier
                
            if firm.get('differentiation_cost', 0) > 0:
                perceived_value += (firm['differentiation_cost'] * 1.5)
                
            if firm.get('ad_spend', 0) > 0:
                ad_boost_multiplier = 1.0 + (firm['ad_spend'] / (firm['ad_spend'] + 500.0))
                perceived_value *= ad_boost_multiplier

            max_allowed_price = 120.0
            perceived_value = min(perceived_value, max_allowed_price)
            
            subjective_bonus = random.gauss(0, 8.0) 
            surplus = (perceived_value + subjective_bonus) - (firm['price'] * sensitivity)
            
            if surplus > max_surplus:
                max_surplus = surplus
                best_firm = firm['id']
                
        if best_firm != 'NO_PURCHASE':
            choices.append((cons['id'], best_firm))
            
    return choices
