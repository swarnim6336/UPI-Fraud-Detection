import streamlit as st
import pandas as pd
import numpy as np
import uuid
from datetime import datetime
import plotly.graph_objects as go
from scoring import calculate_fraud_score, ml_features

st.set_page_config(page_title="UPI Fraud Defender", layout="wide", page_icon="🛡️")

# Custom CSS for a premium look
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_historical_data():
    try:
        df = pd.read_csv('processed_transactions.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

history_df = load_historical_data()

st.title("🛡️ UPI Fraud Detection Engine")
st.markdown("Real-time transaction analysis powered by **Isolation Forest (ML)** and **Time-Series Z-Scores**.")
st.markdown("---")

# Sidebar
st.sidebar.title("💳 Simulate Transaction")
st.sidebar.markdown("Configure an incoming UPI payment below:")

user_id = st.sidebar.selectbox("User ID", [f"user_{i}" for i in range(1, 101)])
amount = st.sidebar.number_input("Transaction Amount (₹)", min_value=1.0, value=1500.0, step=100.0)
category = st.sidebar.selectbox("Merchant Category", ['Grocery', 'Rent', 'Utilities', 'Electronics', 'Entertainment', 'Transfer', 'Unknown'])
location = st.sidebar.text_input("Location", value="Mumbai")
device = st.sidebar.text_input("Device ID", value="device_12345")

submit_btn = st.sidebar.button("Analyze Transaction", type="primary", use_container_width=True)

# Layout: Tabs
tab1, tab2 = st.tabs(["🔴 Live Inference", "👤 User Profiling & History"])

# Filter user history once
if not history_df.empty:
    user_history = history_df[history_df['user_id'] == user_id].sort_values('timestamp')
else:
    user_history = pd.DataFrame()

with tab2:
    st.subheader(f"Historical Profile: {user_id}")
    if not user_history.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Transactions", len(user_history))
        col2.metric("Average Spend", f"₹{user_history['amount'].mean():.2f}")
        col3.metric("Primary Location", user_history['location'].mode()[0] if not user_history['location'].empty else "N/A")
        
        st.markdown("### Recent Transactions")
        st.dataframe(
            user_history[['timestamp', 'amount', 'merchant_category', 'location', 'is_fraud']].tail(10).iloc[::-1], 
            use_container_width=True
        )
    else:
        st.info("No historical data found for this user.")

with tab1:
    if submit_btn:
        with st.spinner("Running through ML Pipeline..."):
            # Real-time feature calculation
            txn_time = pd.to_datetime(datetime.now())
            
            time_since_last = 0
            avg_7d = 0
            txns_1h = 0
            loc_changed = 1
            dev_changed = 1
            
            if not user_history.empty:
                last_txn = user_history.iloc[-1]
                time_since_last = (txn_time - last_txn['timestamp']).total_seconds()
                
                loc_changed = 1 if location != last_txn['location'] else 0
                dev_changed = 1 if device != last_txn['device_id'] else 0
                
                seven_days_ago = txn_time - pd.Timedelta(days=7)
                past_7d = user_history[user_history['timestamp'] >= seven_days_ago]
                if not past_7d.empty:
                    avg_7d = past_7d['amount'].mean()
                    
                one_hour_ago = txn_time - pd.Timedelta(hours=1)
                past_1h = user_history[user_history['timestamp'] >= one_hour_ago]
                txns_1h = len(past_1h)
                
            features_dict = {
                'amount': amount,
                'time_since_last_txn': time_since_last,
                'avg_amount_7d': avg_7d,
                'txns_last_1h': txns_1h,
                'location_changed': loc_changed,
                'device_changed': dev_changed
            }
            
            for feature in ml_features:
                if feature.startswith('merchant_category_'):
                    cat = feature.replace('merchant_category_', '')
                    features_dict[feature] = 1 if category == cat else 0
                    
            # Get Score
            result = calculate_fraud_score(user_id, amount, features_dict)
            score = result['score']
            status = result['status']
            
            st.markdown("### 🧠 AI Analysis Results")
            
            c1, c2 = st.columns([1, 1.5])
            
            with c1:
                # Plotly Gauge Chart
                if status == "CRITICAL":
                    color = "#ff4b4b" # red
                elif status == "WARNING":
                    color = "#ffa500" # orange
                else:
                    color = "#00cc66" # green
                    
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Fraud Risk Score", 'font': {'size': 20}},
                    gauge = {
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': color},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "lightgray",
                        'steps': [
                            {'range': [0, 40], 'color': '#f0f2f6'},
                            {'range': [40, 75], 'color': '#fff3e6'},
                            {'range': [75, 100], 'color': '#ffe6e6'}],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 75}
                    }
                ))
                fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)
                
            with c2:
                st.markdown("#### Decision Breakdown")
                if status == "CRITICAL":
                    st.error("🚨 **TRANSACTION BLOCKED** - High probability of fraud detected.")
                elif status == "WARNING":
                    st.warning("⚠️ **STEP-UP AUTH REQUIRED** - Suspicious patterns detected.")
                else:
                    st.success("✅ **TRANSACTION APPROVED** - Normal behavior.")
                    
                st.markdown("**🔍 Threat Intelligence Signals:**")
                for reason in result['reasons']:
                    if "exceeds" in reason or "Isolation" in reason or "velocity" in reason:
                        st.markdown(f"- 🛑 {reason}")
                    else:
                        st.markdown(f"- 🟢 {reason}")
                        
                st.markdown("---")
                with st.expander("View Extracted Feature Vector"):
                    st.json({
                        "time_since_last_txn (s)": round(time_since_last, 2),
                        "rolling_7d_avg (₹)": round(avg_7d, 2),
                        "txns_in_last_1h": txns_1h,
                        "location_changed": bool(loc_changed),
                        "device_changed": bool(dev_changed)
                    })
    else:
        st.info("👈 Enter transaction details in the sidebar and click **Analyze Transaction** to see the ML model in action.")
