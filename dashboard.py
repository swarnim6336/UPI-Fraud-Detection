import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from scoring import calculate_fraud_score, ml_features

st.set_page_config(page_title="UPI Fraud Detection", layout="wide")

@st.cache_data
def load_historical_data():
    try:
        df = pd.read_csv('processed_transactions.csv')
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

history_df = load_historical_data()

st.title("🚨 Real-Time UPI Fraud Detection")
st.markdown("Submit a live transaction to our Machine Learning pipeline and receive an instant Fraud Risk Score.")

st.sidebar.header("Mock Transaction Entry")

# Pre-filled mock users for the portfolio
user_id = st.sidebar.selectbox("User ID", [f"user_{i}" for i in range(1, 101)])
amount = st.sidebar.number_input("Amount (INR)", min_value=1.0, value=500.0)
category = st.sidebar.selectbox("Merchant Category", ['Grocery', 'Rent', 'Utilities', 'Electronics', 'Entertainment', 'Transfer', 'Unknown'])
location = st.sidebar.text_input("Location", value="Mumbai")
device = st.sidebar.text_input("Device ID", value="device_12345")

if st.sidebar.button("Submit Transaction", type="primary"):
    with st.spinner("Processing transaction via Isolation Forest..."):
        # 1. Prepare timestamp and calculate real-time features
        txn_time = pd.to_datetime(datetime.now())
        
        # Filter user history
        if not history_df.empty:
            user_history = history_df[history_df['user_id'] == user_id].sort_values('timestamp')
        else:
            user_history = pd.DataFrame()
            
        # Initialize features
        time_since_last = 0
        avg_7d = 0
        txns_1h = 0
        loc_changed = 1 # Assume changed for new user
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
                
        # 2. Get Score from scoring engine
        result = calculate_fraud_score(user_id, amount, features_dict)
        
        # 3. Display Results
        st.subheader("Analysis Complete")
        score = result['score']
        
        col1, col2 = st.columns([1, 2])
        with col1:
            # Dynamic metric coloring based on score
            if score >= 75:
                st.error(f"## Risk Score: {score}/100")
                st.error(f"### Status: {result['status']}")
            elif score >= 40:
                st.warning(f"## Risk Score: {score}/100")
                st.warning(f"### Status: {result['status']}")
            else:
                st.success(f"## Risk Score: {score}/100")
                st.success(f"### Status: {result['status']}")
                
        with col2:
            st.markdown("### Decision Reasoning")
            for reason in result['reasons']:
                st.write(f"- {reason}")

st.markdown("---")
st.markdown("*Built for portfolio demonstration. Uses Isolation Forest, IQR Thresholding, and Time-Series Z-Scores.*")
