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
if 'sim_v3' not in st.session_state:
    st.session_state.sim_v3 = InteractiveMarketModel(num_ai_firms=4, num_consumers=2000) 
    st.session_state.sim_v3.step()
    st.session_state.company_cash = 100000.0  # Native bank account

# --- 3. DASHBOARD UI (SIDEBAR) ---
st.sidebar.header("My Company Strategy")

human_firm = st.session_state.sim_v3.human_firm

price_val = st.sidebar.slider("Price ($)", 10.0, 100.0, 40.0, 1.0)
ads_val = st.sidebar.slider("Ad Spend ($/turn)", 0.0, 5000.0, 0.0, 100.0)
inn_val = st.sidebar.slider("Innovation R&D ($/turn)", 0.0, 5000.0, 0.0, 100.0)
diff_val = st.sidebar.slider("Quality (+$ Cost/Unit)", 0.0, 30.0, 0.0, 1.0)

# Wire sliders
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
        # 1. Advance the market simulation
        st.session_state.sim_v3.step()
        
        # 2. OVERWRITE BACKEND RESET: Force live slider values post-step
        human_firm.price = price_val
        human_firm.differentiation_cost = diff_val
        
        # 3. ABSOLUTE BYPASS: Calculate every dollar natively on the frontend
        actual_sales = getattr(human_firm, 'sales', 0)
        
        revenue = actual_sales * price_val
        unit_costs = actual_sales * (20.0 + diff_val) # $20 base cost + Quality slider
        fixed_costs = ads_val + inn_val
        
        true_profit = revenue - unit_costs - fixed_costs
        
        # 4. Apply real math to bank account
        st.session_state.company_cash += true_profit

with col_cash:
    st.metric("🏦 Company Bank Account", f"${st.session_state.company_cash:,.2f}")

if st.session_state.company_cash <= 0:
    st.error("🚨 BANKRUPT! You burned through your cash reserves. Please click 'Reboot app' in the top right menu to restart.")
    st.stop()

# --- 5. SCOREBOARD & GRAPHS ---
st.subheader("Live Market Scoreboard (Current Quarter)")

active_agents = st.session_state.sim_v3.schedule.agents if hasattr(st.session_state.sim_v3, 'schedule') and st.session_state.sim_v3.schedule else st.session_state.sim_v3.agents
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

# Extract graph data
ai_df = st.session_state.sim_v3.datacollector.get_agenttype_vars_dataframe(FirmAgent)
human_df = st.session_state.sim_v3.datacollector.get_agenttype_vars_dataframe(HumanFirm)
firm_df = pd.concat([ai_df, human_df])

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

# --- 6. CUSTOMER ELASTICITY SEGMENTATION (BELOW GRAPHS) ---
st.markdown("---")
st.subheader("🎯 Customer Segment Breakdown (Captured by My Firm)")

consumers = getattr(st.session_state.sim_v3, 'consumers', [])
if consumers:
    firm_states = [{
        'id': a.unique_id, 
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
        total_human_buyers = len(human_buyers)
        
        cons_map = {c['id']: c.get('price_sensitivity', 1.0) if isinstance(c, dict) else getattr(c, 'price_sensitivity', 1.0) for c in consumers}
        
        low_count = sum(1 for cid in human_buyers if cons_map.get(cid, 1.0) < 0.83)
        med_count = sum(1 for cid in human_buyers if 0.83 <= cons_map.get(cid, 1.0) <= 1.17)
        high_count = sum(1 for cid in human_buyers if cons_map.get(cid, 1.0) > 1.17)
        
        if total_human_buyers > 0:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(
                    "Inelastic Buyers (Quality Loyal)", 
                    f"{low_count:,}", 
                    f"{(low_count/total_human_buyers)*100:.1f}% of your buyers",
                    delta_color="off"
                )
            with c2:
                st.metric(
                    "Moderate Buyers (Value Seekers)", 
                    f"{med_count:,}", 
                    f"{(med_count/total_human_buyers)*100:.1f}% of your buyers",
                    delta_color="off"
                )
            with c3:
                st.metric(
                    "High Elasticity (Price Hunters)", 
                    f"{high_count:,}", 
                    f"{(high_count/total_human_buyers)*100:.1f}% of your buyers",
                    delta_color="off"
                )
        else:
            st.info("💡 You currently have 0 sales. Lower your price or boost Marketing/Quality to capture consumer segments.")
    except Exception as e:
        st.caption("Consumer breakdown updating...")

# --- 7. AUTO-RUN LOOP TRIGGER ---
if auto_run:
    time.sleep(0.5) 
    st.rerun()
