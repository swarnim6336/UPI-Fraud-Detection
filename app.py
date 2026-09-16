from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import pandas as pd
import uvicorn
from scoring import calculate_fraud_score, ml_features

app = FastAPI(title="UPI Fraud Detection API")

# Load historical data into memory for real-time feature calculation
# In production, this would be Redis or a fast database
print("Loading historical data into memory...")
try:
    history_df = pd.read_csv('processed_transactions.csv')
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
except:
    history_df = pd.DataFrame()

class Transaction(BaseModel):
    transaction_id: str
    user_id: str
    receiver_id: str
    amount: float
    timestamp: str # ISO format
    merchant_category: str
    device_id: str
    location: str

@app.post("/predict")
def predict_fraud(txn: Transaction):
    try:
        txn_time = pd.to_datetime(txn.timestamp)
        
        # Filter user history
        if not history_df.empty:
            user_history = history_df[history_df['user_id'] == txn.user_id].sort_values('timestamp')
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
            
            # Location and Device checks
            loc_changed = 1 if txn.location != last_txn['location'] else 0
            dev_changed = 1 if txn.device_id != last_txn['device_id'] else 0
            
            # 7-day average
            seven_days_ago = txn_time - pd.Timedelta(days=7)
            past_7d = user_history[user_history['timestamp'] >= seven_days_ago]
            if not past_7d.empty:
                avg_7d = past_7d['amount'].mean()
                
            # 1-hour velocity
            one_hour_ago = txn_time - pd.Timedelta(hours=1)
            past_1h = user_history[user_history['timestamp'] >= one_hour_ago]
            txns_1h = len(past_1h)
            
        # Build features dict for ML model
        features_dict = {
            'amount': txn.amount,
            'time_since_last_txn': time_since_last,
            'avg_amount_7d': avg_7d,
            'txns_last_1h': txns_1h,
            'location_changed': loc_changed,
            'device_changed': dev_changed
        }
        
        # One-hot encode category based on the trained model features
        for feature in ml_features:
            if feature.startswith('merchant_category_'):
                category = feature.replace('merchant_category_', '')
                features_dict[feature] = 1 if txn.merchant_category == category else 0
                
        # Get Score
        result = calculate_fraud_score(txn.user_id, txn.amount, features_dict)
        
        return {
            "transaction_id": txn.transaction_id,
            "user_id": txn.user_id,
            "risk_score": result["score"],
            "status": result["status"],
            "reasons": result["reasons"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
