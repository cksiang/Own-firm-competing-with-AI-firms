import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import time

from interactive import InteractiveMarketModel, HumanFirm
from agent import FirmAgent

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="AI Market Simulator", layout="wide")
st.title("Human vs AI: Live Strategy Simulation")

# --- 2. ROBUST INITIALIZATION ---
# Force a hard reset if the model in memory is an old version without the 'cash' attribute
def initialize_model():
    st.session_state.model = InteractiveMarketModel(num_ai_firms=4, num_consumers=2000) 
    st.session_state.model.step()

if 'model' not in st.session_state:
    initialize_model()
else:
    # Check if the human firm has the new cash attribute. If not, wipe the old memory.
    test_firm = [a for a in st.session_state.model.agents if getattr(a, 'strategy', '') == "My Company (Human)"][0]
    if not hasattr(test_firm, 'cash'):
        initialize_model()

# --- 3. DASHBOARD UI (SIDEBAR) ---
st.sidebar.header("My Company Strategy")

# Extract the human agent DIRECTLY so we can feed it slider data
human_firm = [a for a in st.session_state.model.agents if getattr(a, 'strategy', '') == "My Company (Human)"][0]

price_val = st.sidebar.slider("Price ($)", 10.0, 100.0, 40.0, 1.0)
ads_val = st.sidebar.slider("Ad Spend ($/turn)", 0.0, 5000.0, 0.0, 100.0)
inn_val = st.sidebar.slider("Innovation R&D ($/turn)", 0.0, 5000.0, 0.0, 100.0)
diff_val = st.sidebar.slider("Quality (+$ Cost/Unit)", 0.0, 30.0, 0.0, 1.0)

# Wire sliders directly to the human firm
human_firm.target_price = price_val
human_firm.target_ads = ads_val
human_firm.target_inn = inn_val
human_firm.target_diff = diff_val

# --- 4. ADVANCE SIMULATION & BANK UI ---
# We create 3 columns on the main screen to hold the button, auto-run, and bank balance
col_btn, col_auto, col_cash = st.columns([1, 1, 1])

with col_btn:
    step_pressed = st.button("Advance 1 Quarter")
with col_auto:
    auto_run = st.checkbox("Auto-Run (Live Market Mode)")

# Calculate the math FIRST
if step_pressed or auto_run:
    with st.spinner("Processing 2,000 parallel consumer decisions..."):
        st.session_state.model.step()

# Read the cash AFTER the math finishes to prevent UI lag
human_firm = [a for a in st.session_state.model.agents if getattr(a, 'strategy', '') == "My Company (Human)"][0]
is_bankrupt = getattr(human_firm, 'is_bankrupt', False)
current_cash = getattr(human_firm, 'cash', 100000.0)

# Display the cash on the main screen
with col_cash:
    st.metric("🏦 Company Bank Account", f"${current_cash:,.2f}")

# Bankruptcy Lockout
if is_bankrupt:
    st.error("🚨 BANKRUPT! Game Over. You burned through your cash reserves. Please click 'Reboot app' in the top right menu to start over.")
    st.stop() # Halts the graphs and prevents further turns

# --- 5. SAFE DATA EXTRACTION & PLOTTING ---
ai_df = st.session_state.model.datacollector.get_agenttype_vars_dataframe(FirmAgent)
human_df = st.session_state.model.datacollector.get_agenttype_vars_dataframe(HumanFirm)
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
# This must be at the very bottom so the graphs draw BEFORE it loops!
if auto_run:
    time.sleep(0.5) 
    st.rerun()
