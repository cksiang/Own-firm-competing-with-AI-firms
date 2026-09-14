import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import time

from interactive import InteractiveMarketModel, HumanFirm
from agent import FirmAgent
from agent_execution import batch_consumer_choice

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="AI Market Simulator", layout="wide")
st.title("Human vs AI: Live Strategy Simulation")

# --- 2. NATIVE STATE INITIALIZATION ---
if 'sim_v9' not in st.session_state:
    st.session_state.sim_v9 = InteractiveMarketModel(num_ai_firms=4, num_consumers=2000) 
    st.session_state.sim_v9.step()
    st.session_state.company_cash = 100000.0  

# --- 3. DASHBOARD UI (SIDEBAR) ---
st.sidebar.header("My Company Strategy")

# Fixed: Now properly references sim_v9
human_firm = st.session_state.sim_v9.human_firm

price_val = st.sidebar.slider("Price ($)", 10.0, 100.0, 40.0, 1.0)
ads_val = st.sidebar.slider("Ad Spend ($/turn)", 0.0, 5000.0, 0.0, 100.0)
inn_val = st.sidebar.slider("Innovation R&D ($/turn)", 0.0, 5000.0, 0.0, 100.0)
diff_val = st.sidebar.slider("Quality (+$ Cost/Unit)", 0.0, 30.0, 0.0, 1.0)

human_firm.target_price = price_val
human_firm.target_ads = ads_val
human_firm.target_inn = inn_val
human_firm.target_diff = diff_val

# --- 4. ADVANCE SIMULATION & BANK UI ---
col_btn, col_auto, col_cash = st.columns([1, 1, 1])

with col_btn:
    step_pressed = st.button("Advance 1 Quarter")
with col_auto:
    auto_run = st.checkbox("Auto-Run (Live Market Mode)")

if step_pressed or auto_run:
    with st.spinner("Processing market quarter..."):
        st.session_state.sim_v9.step()
        
        human_firm.price = price_val
        human_firm.differentiation_cost = diff_val
        
        actual_sales = getattr(human_firm, 'sales', 0)
        revenue = actual_sales * price_val
        unit_costs = actual_sales * (20.0 + diff_val)
        fixed_costs = ads_val + inn_val
        true_profit = revenue - unit_costs - fixed_costs
        
        st.session_state.company_cash += true_profit

with col_cash:
    st.metric("🏦 Company Bank Account", f"${st.session_state.company_cash:,.2f}")

if st.session_state.company_cash <= 0:
    st.error("🚨 BANKRUPT! You burned through your cash reserves. Please click 'Reboot app' in the menu.")
    st.stop()

# --- 5. SCOREBOARD & GRAPHS ---
st.subheader("Live Market Scoreboard (Current Quarter)")

active_agents = st.session_state.sim_v9.schedule.agents if hasattr(st.session_state.sim_v9, 'schedule') and st.session_state.sim_v9.schedule else st.session_state.sim_v9.agents
total_sales = sum([getattr(a, 'sales', 0) for a in active_agents])

scoreboard_data = []
for a in active_agents:
    sales = getattr(a, 'sales', 0)
    share = (sales / total_sales * 100) if total_sales > 0 else 0
    unit_cost = 20.0 + getattr(a, 'differentiation_cost', 0.0)
    
    scoreboard_data.append({
        "Firm": getattr(a, 'strategy', 'Unknown Firm'),
        "Price": f"${getattr(a, 'price', 0.0):.2f}",
        "Unit Cost": f"${unit_cost:.2f}",
        "Units Sold": f"{sales:,}",
        "Market Share": f"{share:.1f}%"
    })

st.table(pd.DataFrame(scoreboard_data).set_index("Firm"))

firm_df = st.session_state.sim_v9.datacollector.get_agent_vars_dataframe()

if not firm_df.empty:
    df_reset = firm_df.reset_index()
    sales_data = df_reset.pivot_table(index='Step', columns='Strategy', values='Sales', aggfunc='sum').fillna(0)
    market_share = sales_data.div(sales_data.sum(axis=1), axis=0) * 100
    market_share = market_share.fillna(0)
    
    profit_data = df_reset.pivot_table(index='Step', columns='Strategy', values='Profit', aggfunc='sum').fillna(0)
    
    if not market_share.empty and not market_share.columns.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig_share, ax_share = plt.subplots(figsize=(8, 5))
            market_share.plot(ax=ax_share, kind='area', alpha=0.7, legend=False)
            ax_share.set_title("Live Market Share (Elasticity)")
            ax_share.set_ylabel("Share (%)")
            st.pyplot(fig_share)
            
        with col2:
            fig_profit, ax_profit = plt.subplots(figsize=(8, 5))
            profit_data.plot(ax=ax_profit, linewidth=2)
            ax_profit.set_title("Live Profitability")
            ax_profit.set_ylabel("Total Profit ($)")
            ax_profit.legend(title="Firms", loc='upper left', fontsize='small')
            st.pyplot(fig_profit)

# --- 6. DUAL CONSUMER ELASTICITY INTELLIGENCE ---
st.markdown("---")
st.subheader("📊 Consumer Elasticity Intelligence")

consumers = getattr(st.session_state.sim_v9, 'consumers', [])
if consumers:
    total_cons = len(consumers)
    
    def extract_sens(c):
        return c.get('price_sensitivity', 1.0) if isinstance(c, dict) else getattr(c, 'price_sensitivity', 1.0)

    tot_low = sum(1 for c in consumers if extract_sens(c) < 0.83)
    tot_med = sum(1 for c in consumers if 0.83 <= extract_sens(c) <= 1.17)
    tot_high = sum(1 for c in consumers if extract_sens(c) > 1.17)

    firm_states = [{
        'id': getattr(a, 'unique_id', 0), 
        'price': getattr(a, 'price', 40.0), 
        'strategy': getattr(a, 'strategy', ''),
        'ad_spend': getattr(a, 'ad_spend', 0.0),
        'innovation_spend': getattr(a, 'innovation_spend', 0.0),
        'differentiation_cost': getattr(a, 'differentiation_cost', 0.0)
    } for a in active_agents]
    
    try:
        choices = batch_consumer_choice(consumers, firm_states)
        human_id = human_firm.unique_id
        human_buyers = [cons_id for cons_id, firm_id in choices if firm_id == human_id]
        
        cons_map = {c['id']: extract_sens(c) for c in consumers}
        
        cap_low = sum(1 for cid in human_buyers if cons_map.get(cid, 1.0) < 0.83)
        cap_med = sum(1 for cid in human_buyers if 0.83 <= cons_map.get(cid, 1.0) <= 1.17)
        cap_high = sum(1 for cid in human_buyers if cons_map.get(cid, 1.0) > 1.17)
        
        col_total, col_captured = st.columns(2)
        
        with col_total:
            st.markdown("#### 🌐 Total Market Demand (2,000 Consumers)")
            tm1, tm2, tm3 = st.columns(3)
            tm1.metric("Low Elasticity (Brand Loyal)", f"{tot_low:,}", f"{(tot_low/total_cons)*100:.1f}% Market", delta_color="off")
            tm2.metric("Moderate Elasticity (Balanced)", f"{tot_med:,}", f"{(tot_med/total_cons)*100:.1f}% Market", delta_color="off")
            tm3.metric("High Elasticity (Price Sensitive)", f"{tot_high:,}", f"{(tot_high/total_cons)*100:.1f}% Market", delta_color="off")

        with col_captured:
            st.markdown("#### 🎯 Captured by My Firm")
            if len(human_buyers) > 0:
                cm1, cm2, cm3 = st.columns(3)
                cm1.metric("Loyal Captured", f"{cap_low:,}", f"{(cap_low/tot_low)*100:.1f}% of segment", delta_color="off")
                cm2.metric("Balanced Captured", f"{cap_med:,}", f"{(cap_med/tot_med)*100:.1f}% of segment", delta_color="off")
                cm3.metric("Price Hunters Captured", f"{cap_high:,}", f"{(cap_high/tot_high)*100:.1f}% of segment", delta_color="off")
            else:
                st.info("💡 0 Buyers Captured — Adjust price, quality, or ad spend to penetrate consumer segments.")
                
    except Exception as e:
        st.caption("Consumer breakdown updating...")

if auto_run:
    time.sleep(0.5) 
    st.rerun()
