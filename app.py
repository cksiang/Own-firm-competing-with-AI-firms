import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from interactive import InteractiveMarketModel, HumanFirm
from agent import FirmAgent

# 1. Page Config
st.set_page_config(page_title="AI Market Simulator", layout="wide")
st.title("Human vs AI: Live Strategy Simulation")

# 2. Initialize the model in the background (Session State keeps it alive between clicks)
if 'model' not in st.session_state:
    st.session_state.model = InteractiveMarketModel(num_ai_firms=4, num_consumers=10000)

# 3. Create the Web Sliders (Sidebar or Columns)
st.sidebar.header("My Company Strategy")
price_val = st.sidebar.slider("Price ($)", 10.0, 100.0, 40.0, 1.0)
ads_val = st.sidebar.slider("Ad Spend ($/turn)", 0.0, 5000.0, 0.0, 100.0)
inn_val = st.sidebar.slider("Innovation R&D ($/turn)", 0.0, 5000.0, 0.0, 100.0)
diff_val = st.sidebar.slider("Quality (+$ Cost/Unit)", 0.0, 30.0, 0.0, 1.0)

# Update human firm target variables
st.session_state.model.human_target_price = price_val
st.session_state.model.human_target_ads = ads_val
st.session_state.model.human_target_inn = inn_val
st.session_state.model.human_target_diff = diff_val

# 4. Advance the Simulation
if st.button("Advance Market 1 Quarter (Step)"):
    st.session_state.model.step()

# 5. Extract Data and Draw Matplotlib Graphs
ai_df = st.session_state.model.datacollector.get_agenttype_vars_dataframe(FirmAgent)
human_df = st.session_state.model.datacollector.get_agenttype_vars_dataframe(HumanFirm)
firm_df = pd.concat([ai_df, human_df])

if not firm_df.empty:
    df_reset = firm_df.reset_index()
    market_share = df_reset.pivot_table(index='Step', columns='Strategy', values='Sales', aggfunc='sum')
    market_share = market_share.div(market_share.sum(axis=1), axis=0) * 100
    
    fig, ax = plt.subplots(figsize=(10, 5))
    market_share.plot(ax=ax, kind='area', alpha=0.7)
    ax.set_title("Market Share (Demand Elasticity)")
    
    # Render the plot in the browser
    st.pyplot(fig)
