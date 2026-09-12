import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from interactive import InteractiveMarketModel, HumanFirm
from agent import FirmAgent

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="AI Market Simulator", layout="wide")
st.title("Human vs AI: Live Strategy Simulation")

# --- 2. ROBUST INITIALIZATION ---
# Initialize the model and force it to take Step 1 immediately so charts never crash on load
if 'model' not in st.session_state:
    # Lowered consumers to 2000 to ensure the free cloud server doesn't time out
    st.session_state.model = InteractiveMarketModel(num_ai_firms=4, num_consumers=2000) 
    st.session_state.model.step() 

# --- 3. DASHBOARD UI (SIDEBAR) ---
st.sidebar.header("My Company Strategy")
price_val = st.sidebar.slider("Price ($)", 10.0, 100.0, 40.0, 1.0)
ads_val = st.sidebar.slider("Ad Spend ($/turn)", 0.0, 5000.0, 0.0, 100.0)
inn_val = st.sidebar.slider("Innovation R&D ($/turn)", 0.0, 5000.0, 0.0, 100.0)
diff_val = st.sidebar.slider("Quality (+$ Cost/Unit)", 0.0, 30.0, 0.0, 1.0)

# Apply sliders to the model
st.session_state.model.human_target_price = price_val
st.session_state.model.human_target_ads = ads_val
st.session_state.model.human_target_inn = inn_val
st.session_state.model.human_target_diff = diff_val

# --- 4. ADVANCE SIMULATION ---
if st.button("Advance Market 1 Quarter (Step)"):
    with st.spinner("Processing 2,000 parallel consumer decisions..."):
        st.session_state.model.step()

# --- 5. SAFE DATA EXTRACTION & PLOTTING ---
ai_df = st.session_state.model.datacollector.get_agenttype_vars_dataframe(FirmAgent)
human_df = st.session_state.model.datacollector.get_agenttype_vars_dataframe(HumanFirm)
firm_df = pd.concat([ai_df, human_df])

# Bulletproof check: Only attempt to plot if we successfully extracted data
if not firm_df.empty:
    df_reset = firm_df.reset_index()
    
    # Process Data with safeguards against NaN and duplicates
    sales_data = df_reset.pivot_table(index='Step', columns='Strategy', values='Sales', aggfunc='sum').fillna(0)
    market_share = sales_data.div(sales_data.sum(axis=1), axis=0) * 100
    market_share = market_share.fillna(0)
    
    profit_data = df_reset.pivot_table(index='Step', columns='Strategy', values='Profit', aggfunc='sum').fillna(0)
    
    # Final safety check before handing to Matplotlib
    if not market_share.empty and not market_share.columns.empty:
        col1, col2 = st.columns(2) # Display graphs side-by-side
        
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
