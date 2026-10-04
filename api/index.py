from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime

app = FastAPI(title="UPI Fraud API")

# Add CORS to allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Serve the static frontend UI
app.mount("/public", StaticFiles(directory=os.path.join(base_dir, "public")), name="public")

@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(base_dir, "public", "index.html"))

# Load artifacts
try:
    iso_forest = joblib.load(os.path.join(base_dir, 'isolation_forest.joblib'))
    ml_features = joblib.load(os.path.join(base_dir, 'model_features.joblib'))
    zscore_params = joblib.load(os.path.join(base_dir, 'zscore_params.joblib'))
    iqr_df = pd.read_csv(os.path.join(base_dir, 'iqr_thresholds.csv')).set_index('user_id')
    history_df = pd.read_csv(os.path.join(base_dir, 'processed_transactions.csv'))
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
except Exception as e:
    print(f"Error loading artifacts: {e}")
    history_df = pd.DataFrame()
    ml_features = []

class Transaction(BaseModel):
    user_id: str
    amount: float
    merchant_category: str
    device_id: str
    location: str

def calculate_fraud_score(user_id, amount, features_dict):
    reasons = []
    score = 0
    
    # 1. IQR
    try:
        if user_id in iqr_df.index:
            upper_bound = iqr_df.loc[user_id, 'Upper_Bound']
            if amount > upper_bound:
                score += 40
                reasons.append(f"Amount (₹{amount}) exceeds historical normal limits.")
        else:
            if amount > 10000:
                score += 20
                reasons.append("High amount for previously unseen user.")
    except: pass
            
    # 2. Z-Score
    try:
        vel_mean = zscore_params.get('velocity_mean', 0)
        vel_std = zscore_params.get('velocity_std', 1)
        txns_1h = features_dict.get('txns_last_1h', 0)
        z_score = (txns_1h - vel_mean) / (vel_std + 1e-5)
        if z_score > 2.0:
            score += 20
            reasons.append(f"Unusual transaction velocity (Z-Score: {z_score:.2f}).")
    except: pass
        
    # 3. Isolation Forest
    try:
        X_input = pd.DataFrame([features_dict], columns=ml_features).fillna(0)
        prediction = iso_forest.predict(X_input)[0]
        if prediction == -1:
            score += 40
            reasons.append("Machine Learning Isolation Forest flagged behavioral anomaly.")
    except: pass
        
    score = min(score, 100)
    if score >= 75:
        status = "CRITICAL"
    elif score >= 40:
        status = "WARNING"
    else:
        status = "APPROVED"
        if len(reasons) == 0:
            reasons.append("Transaction falls within normal parameters.")
            
    return {"score": score, "status": status, "reasons": reasons}


@app.post("/api/predict")
def predict_fraud(txn: Transaction):
    try:
        txn_time = pd.to_datetime(datetime.now())
        
        if not history_df.empty:
            user_history = history_df[history_df['user_id'] == txn.user_id].sort_values('timestamp')
        else:
            user_history = pd.DataFrame()
            
        time_since_last = 0
        avg_7d = 0
        txns_1h = 0
        loc_changed = 1
        dev_changed = 1
        
        if not user_history.empty:
            last_txn = user_history.iloc[-1]
            time_since_last = (txn_time - last_txn['timestamp']).total_seconds()
            loc_changed = 1 if txn.location != last_txn['location'] else 0
            dev_changed = 1 if txn.device_id != last_txn['device_id'] else 0
            
            seven_days_ago = txn_time - pd.Timedelta(days=7)
            past_7d = user_history[user_history['timestamp'] >= seven_days_ago]
            if not past_7d.empty:
                avg_7d = past_7d['amount'].mean()
                
            one_hour_ago = txn_time - pd.Timedelta(hours=1)
            past_1h = user_history[user_history['timestamp'] >= one_hour_ago]
            txns_1h = len(past_1h)
            
        features_dict = {
            'amount': txn.amount,
            'time_since_last_txn': time_since_last,
            'avg_amount_7d': avg_7d,
            'txns_last_1h': txns_1h,
            'location_changed': loc_changed,
            'device_changed': dev_changed
        }
        
        for feature in ml_features:
            if feature.startswith('merchant_category_'):
                cat = feature.replace('merchant_category_', '')
                features_dict[feature] = 1 if txn.merchant_category == cat else 0
                
        result = calculate_fraud_score(txn.user_id, txn.amount, features_dict)
        
        # Include feature vector for frontend display
        result['feature_vector'] = {
            "time_since_last_txn": round(time_since_last, 2),
            "avg_amount_7d": round(avg_7d, 2),
            "txns_last_1h": txns_1h,
            "location_changed": bool(loc_changed),
            "device_changed": bool(dev_changed)
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
