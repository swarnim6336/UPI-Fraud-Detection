import streamlit as st
import pandas as pd
import numpy as np
import uuid
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from scoring import calculate_fraud_score, ml_features

# Page Config MUST be the very first Streamlit command
st.set_page_config(page_title="Ironclad AI | UPI Fraud Defender", layout="wide", page_icon="🛡️")

# --- CUSTOM CSS FOR CYBERSECURITY THEME ---
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0b0f19;
        color: #e0e6ed;
    }
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 800;
        color: #00e5ff;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #8b9eb3;
        font-weight: 600;
    }
    
    /* Card Layouts */
    .css-1r6slb0 {
        background-color: #121826;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* Neon Accents */
    .highlight-text {
        color: #00e5ff;
        text-shadow: 0 0 5px rgba(0,229,255,0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- CACHE DATA LOADING ---
@st.cache_data
def load_historical_data():
    try:
        df = pd.read_csv('processed_transactions.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

history_df = load_historical_data()

# --- HEADER SECTION ---
col_logo, col_title = st.columns([1, 8])
with col_title:
    st.markdown("<h1><span class='highlight-text'>IRONCLAD AI</span> // UPI FRAUD NEURAL ENGINE</h1>", unsafe_allow_html=True)
    st.markdown("Real-time behavioral anomaly detection powered by **Isolation Forest** & **Time-Series Analysis**.")
st.markdown("---")

# --- SIDEBAR: SIMULATION CONTROL PANEL ---
st.sidebar.markdown("### 🎛️ INFERENCE CONTROLS")
st.sidebar.markdown("Inject a simulated UPI transaction into the neural engine.")

user_id = st.sidebar.selectbox("👤 Target User ID", [f"user_{i}" for i in range(1, 101)])
amount = st.sidebar.slider("💸 Transaction Amount (₹)", min_value=10.0, max_value=50000.0, value=1500.0, step=100.0)
category = st.sidebar.selectbox("🛒 Merchant Category", ['Grocery', 'Rent', 'Utilities', 'Electronics', 'Entertainment', 'Transfer', 'Unknown'])
location = st.sidebar.text_input("📍 Location Data", value="Mumbai")
device = st.sidebar.text_input("📱 Device Fingerprint", value="device_12345")

submit_btn = st.sidebar.button("🚀 EXECUTE INFERENCE", type="primary", use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.markdown("<small>System Status: ONLINE 🟢</small>", unsafe_allow_html=True)

# Filter user history once
if not history_df.empty:
    user_history = history_df[history_df['user_id'] == user_id].sort_values('timestamp')
else:
    user_history = pd.DataFrame()

# --- MAIN DASHBOARD LAYOUT ---
if submit_btn:
    with st.spinner("Analyzing behavioral nodes..."):
        # 1. Real-time feature calculation
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
                
        # 2. Get Score
        result = calculate_fraud_score(user_id, amount, features_dict)
        score = result['score']
        status = result['status']
        
        # Determine styling based on status
        if status == "CRITICAL":
            color = "#ff2b2b" # Neon Red
            bg_color = "rgba(255, 43, 43, 0.1)"
            status_icon = "🛑"
        elif status == "WARNING":
            color = "#ffb82b" # Neon Orange
            bg_color = "rgba(255, 184, 43, 0.1)"
            status_icon = "⚠️"
        else:
            color = "#00e5ff" # Neon Cyan
            bg_color = "rgba(0, 229, 255, 0.1)"
            status_icon = "✅"

        # --- ROW 1: SCORE & RADAR CHART ---
        col1, col2, col3 = st.columns([1.2, 1.5, 1])
        
        with col1:
            st.markdown("### 🎯 Risk Assessment")
            # Custom Gauge using Plotly
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = score,
                number = {'font': {'size': 60, 'color': color}},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#8b9eb3"},
                    'bar': {'color': color, 'line': {'color': "white", 'width': 2}},
                    'bgcolor': "#121826",
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, 40], 'color': 'rgba(0, 229, 255, 0.1)'},
                        {'range': [40, 75], 'color': 'rgba(255, 184, 43, 0.1)'},
                        {'range': [75, 100], 'color': 'rgba(255, 43, 43, 0.1)'}],
                    'threshold': {'line': {'color': "#ff2b2b", 'width': 4}, 'thickness': 0.75, 'value': 75}
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font={'color': "#e0e6ed", 'family': "Courier New"},
                height=300,
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            st.markdown(f"<div style='text-align: center; padding: 10px; background-color: {bg_color}; border-radius: 5px; border: 1px solid {color};'><h3 style='color: {color}; margin: 0;'>{status_icon} {status}</h3></div>", unsafe_allow_html=True)
            
        with col2:
            st.markdown("### 🕸️ Behavioral Radar")
            # Normalize values for radar chart comparison
            radar_categories = ['Amount', 'Velocity (1h)', 'Avg Spend (7d)', 'Location Flag', 'Device Flag']
            # Scale values relative to expected baselines purely for visualization
            norm_amount = min(amount / (avg_7d + 1), 5) * 20
            norm_vel = min(txns_1h, 10) * 10
            norm_avg = 50 # Baseline
            norm_loc = loc_changed * 100
            norm_dev = dev_changed * 100
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=[norm_amount, norm_vel, norm_avg, norm_loc, norm_dev],
                theta=radar_categories,
                fill='toself',
                fillcolor='rgba(0, 229, 255, 0.2)',
                line=dict(color='#00e5ff', width=2),
                name='Current Txn'
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=False, range=[0, 100]),
                    bgcolor="#121826"
                ),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                font={'color': "#8b9eb3"},
                height=350,
                margin=dict(l=40, r=40, t=20, b=20)
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        with col3:
            st.markdown("### 🔍 Model Explainability")
            st.markdown("<br>", unsafe_allow_html=True)
            for reason in result['reasons']:
                if "exceeds" in reason or "Isolation" in reason or "velocity" in reason:
                    st.markdown(f"<div style='padding:10px; margin-bottom:10px; border-left: 4px solid #ff2b2b; background: rgba(255,43,43,0.1);'>{reason}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='padding:10px; margin-bottom:10px; border-left: 4px solid #00e5ff; background: rgba(0,229,255,0.1);'>{reason}</div>", unsafe_allow_html=True)
            
            with st.expander("Show Raw Feature Vector ⚙️"):
                st.json({
                    "time_gap_seconds": round(time_since_last, 2),
                    "rolling_7d_avg_amount": round(avg_7d, 2),
                    "txn_velocity_1h": txns_1h,
                    "is_new_location": bool(loc_changed),
                    "is_new_device": bool(dev_changed)
                })

    # --- ROW 2: HISTORICAL CONTEXT ---
    st.markdown("---")
    st.markdown("### 📈 Subject Historical Timeline")
    if not user_history.empty:
        # Time-series chart of last 20 transactions
        recent_txns = user_history.tail(30)
        fig_line = px.line(
            recent_txns, x='timestamp', y='amount', 
            markers=True, 
            color_discrete_sequence=['#00e5ff'],
            hover_data=['merchant_category', 'location']
        )
        # Add the current simulated transaction to the chart in red
        fig_line.add_scatter(
            x=[txn_time], y=[amount], 
            mode='markers', marker=dict(color=color, size=12, symbol='star'),
            name='Current Simulation'
        )
        
        fig_line.update_layout(
            plot_bgcolor="#121826",
            paper_bgcolor="rgba(0,0,0,0)",
            font={'color': "#8b9eb3"},
            xaxis_title="Timeline",
            yaxis_title="Transaction Amount (₹)",
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            hovermode="x unified"
        )
        fig_line.update_xaxes(showgrid=False)
        fig_line.update_yaxes(gridcolor='#1e293b')
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("No historical timeline available for this subject.")

else:
    # --- IDLE STATE ---
    st.info("👈 System Idle. Configure transaction parameters in the sidebar and execute inference.")
    
    # Show user stats in idle mode
    if not user_history.empty:
        st.markdown("### 👤 Subject Overview")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Historical Txns", len(user_history))
        c2.metric("Historical Avg Spend", f"₹{user_history['amount'].mean():.2f}")
        c3.metric("Primary Location", user_history['location'].mode()[0] if not user_history['location'].empty else "N/A")
        
        fraud_count = user_history['is_fraud'].sum()
        c4.metric("Past Fraud Incidents", fraud_count)
