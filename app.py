import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import time

from interactive import InteractiveMarketModel, HumanFirm
from agent import FirmAgent

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="AI Market Simulator", layout="wide")
st.title("Human vs AI: Live Strategy Simulation")

# --- 2. NATIVE STATE INITIALIZATION ---
# We bypass the backend cache by storing the cash directly in Streamlit's native memory
if 'sim_v3' not in st.session_state:
    st.session_state.sim_v3 = InteractiveMarketModel(num_ai_firms=4, num_consumers=2000) 
    st.session_state.sim_v3.step()
    st.session_state.company_cash = 100000.0  # The native bank account

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
        
        # 2. ABSOLUTE BYPASS: Calculate every dollar natively on the frontend
        # We grab your actual sales volume, but do the financial math ourselves
        actual_sales = getattr(human_firm, 'sales', 0)
        
        revenue = actual_sales * price_val
        unit_costs = actual_sales * (20.0 + diff_val) # $20 base cost + Quality slider
        fixed_costs = ads_val + inn_val
        
        true_profit = revenue - unit_costs - fixed_costs
        
        # 3. Apply the real math to your bank account
        st.session_state.company_cash += true_profit

with col_cash:
    st.metric("🏦 Company Bank Account", f"${st.session_state.company_cash:,.2f}")

if st.session_state.company_cash <= 0:
    st.error("🚨 BANKRUPT! You burned through your cash reserves. Please click 'Reboot app' in the top right menu to restart.")
    st.stop()
# --- 5. SAFE DATA EXTRACTION & PLOTTING ---
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

# --- 6. AUTO-RUN LOOP TRIGGER ---
if auto_run:
    time.sleep(0.5) 
    st.rerun()
