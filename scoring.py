import joblib
import pandas as pd
import numpy as np
import os

# Load artifacts globally
ml_features = []
try:
    iso_forest = joblib.load('isolation_forest.joblib')
    ml_features = joblib.load('model_features.joblib')
    zscore_params = joblib.load('zscore_params.joblib')
    iqr_df = pd.read_csv('iqr_thresholds.csv').set_index('user_id')
except Exception as e:
    print(f"Warning: Artifacts not found or error loading them. {e}")

def calculate_fraud_score(user_id, amount, features_dict):
    """
    Combines 3 models to output a score (0-100).
    """
    reasons = []
    score = 0
    
    # 1. IQR (Statistical Rule-Based)
    if user_id in iqr_df.index:
        upper_bound = iqr_df.loc[user_id, 'Upper_Bound']
        if amount > upper_bound:
            score += 40
            reasons.append(f"Amount (₹{amount}) exceeds historical normal limits for this user.")
    else:
        # New user heuristic
        if amount > 10000:
            score += 20
            reasons.append("High amount for a previously unseen user.")
            
    # 2. Time-Series Tracking (Z-Score)
    vel_mean = zscore_params.get('velocity_mean', 0)
    vel_std = zscore_params.get('velocity_std', 1)
    txns_1h = features_dict.get('txns_last_1h', 0)
    
    # Calculate Z-score for transaction velocity
    z_score = (txns_1h - vel_mean) / (vel_std + 1e-5)
    if z_score > 2.0:
        score += 20
        reasons.append(f"Unusual transaction velocity (Z-Score: {z_score:.2f}).")
        
    # 3. Isolation Forest (Machine Learning)
    # Prepare features in the exact order the model expects
    X_input = pd.DataFrame([features_dict], columns=ml_features).fillna(0)
    prediction = iso_forest.predict(X_input)[0]
    
    if prediction == -1: # -1 indicates anomaly in IsolationForest
        score += 40
        reasons.append("Machine Learning Isolation Forest flagged behavioral anomaly.")
        
    # Cap score at 100
    score = min(score, 100)
    
    # Determine Status
    if score >= 75:
        status = "CRITICAL"
    elif score >= 40:
        status = "WARNING"
    else:
        status = "APPROVED"
        if len(reasons) == 0:
            reasons.append("Transaction falls within normal parameters.")
            
    return {
        "score": score,
        "status": status,
        "reasons": reasons
    }
