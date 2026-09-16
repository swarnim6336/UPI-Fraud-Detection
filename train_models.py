import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

def train_models(input_file='processed_transactions.csv'):
    print("Loading preprocessed data...")
    df = pd.read_csv(input_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # --- 1. IQR Model (Statistical Rule-Based) ---
    print("1. Calculating IQR historical thresholds for each user...")
    user_stats = df.groupby('user_id')['amount'].agg(
        Q1=lambda x: np.percentile(x, 25),
        Q3=lambda x: np.percentile(x, 75)
    ).reset_index()
    user_stats['IQR'] = user_stats['Q3'] - user_stats['Q1']
    user_stats['Upper_Bound'] = user_stats['Q3'] + 1.5 * user_stats['IQR']
    
    # If IQR is 0, add a small buffer so the upper bound isn't too strict
    user_stats['Upper_Bound'] = np.where(user_stats['IQR'] == 0, user_stats['Q3'] * 1.5, user_stats['Upper_Bound'])
    user_stats.to_csv('iqr_thresholds.csv', index=False)
    
    # --- 2. Isolation Forest (Machine Learning) ---
    print("2. Training Isolation Forest model...")
    # Select features for ML
    ml_features = ['amount', 'time_since_last_txn', 'avg_amount_7d', 'txns_last_1h', 'location_changed', 'device_changed']
    cat_features = [col for col in df.columns if col.startswith('merchant_category_')]
    features = ml_features + cat_features
    
    X = df[features].fillna(0)
    
    # Train Isolation Forest. We expect around 5% anomalies based on our simulation
    iso_forest = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    iso_forest.fit(X)
    
    # Save the model and the feature list so the API knows what to expect
    joblib.dump(iso_forest, 'isolation_forest.joblib')
    joblib.dump(features, 'model_features.joblib')
    
    # Let's evaluate quickly on the dataset
    df['iforest_pred'] = iso_forest.predict(X)
    df['iforest_flag'] = df['iforest_pred'] == -1
    
    # --- 3. Time-Series Tracking (Z-score thresholds) ---
    print("3. Calculating Time-Series Z-score baselines...")
    global_velocity_mean = df['txns_last_1h'].mean()
    global_velocity_std = df['txns_last_1h'].std()
    
    zscore_params = {
        'velocity_mean': float(global_velocity_mean),
        'velocity_std': float(global_velocity_std)
    }
    joblib.dump(zscore_params, 'zscore_params.joblib')
    
    # Quick Summary
    correct_flags = df[(df['is_fraud'] == 1) & (df['iforest_flag'] == True)].shape[0]
    total_fraud = df[df['is_fraud'] == 1].shape[0]
    print(f"\nIsolation Forest successfully caught {correct_flags}/{total_fraud} fraud cases.")
    
    print("\nModel training complete! Artifacts saved:")
    print(" - iqr_thresholds.csv (Statistical Model)")
    print(" - isolation_forest.joblib (ML Model)")
    print(" - model_features.joblib (API Requirements)")
    print(" - zscore_params.joblib (Time-Series Rules)")
    
if __name__ == "__main__":
    train_models()
