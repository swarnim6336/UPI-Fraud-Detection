import pandas as pd
import numpy as np

def preprocess_data(input_file='upi_transactions.csv', output_file='processed_transactions.csv'):
    print("Loading data...")
    df = pd.read_csv(input_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 1. Sort by user and time to compute sequential features
    df = df.sort_values(by=['user_id', 'timestamp'])
    
    # Time since user's last transaction (in seconds)
    df['time_since_last_txn'] = df.groupby('user_id')['timestamp'].diff().dt.total_seconds().fillna(0)
    
    # Location and device change flags
    df['last_location'] = df.groupby('user_id')['location'].shift(1).fillna(df['location'])
    df['location_changed'] = (df['location'] != df['last_location']).astype(int)
    
    df['last_device'] = df.groupby('user_id')['device_id'].shift(1).fillna(df['device_id'])
    df['device_changed'] = (df['device_id'] != df['last_device']).astype(int)
    
    df = df.drop(columns=['last_location', 'last_device'])
    
    # 2. Time-window features (7-day average, 1-hour count)
    print("Calculating rolling features...")
    df = df.set_index('timestamp')
    
    # We use closed='left' to exclude the current transaction from the historical average
    roll_sum = df.groupby('user_id')['amount'].apply(lambda x: x.rolling('7D', closed='left').sum()).fillna(0).values
    roll_count = df.groupby('user_id')['amount'].apply(lambda x: x.rolling('7D', closed='left').count()).fillna(0).values
    
    df['avg_amount_7d'] = np.where(roll_count > 0, roll_sum / roll_count, 0)
    
    roll_1h_count = df.groupby('user_id')['amount'].apply(lambda x: x.rolling('1h', closed='left').count()).fillna(0).values
    df['txns_last_1h'] = roll_1h_count
    
    df = df.reset_index()
    
    # 3. Category encoding (One-Hot)
    df = pd.get_dummies(df, columns=['merchant_category'], drop_first=False)
    
    # Clean up boolean columns created by get_dummies to integers
    for col in df.columns:
        if df[col].dtype == bool:
            df[col] = df[col].astype(int)
            
    df.to_csv(output_file, index=False)
    print(f"Preprocessing complete. Saved {len(df)} records to {output_file}")
    
    print("\nSample of engineered features:")
    print(df[['user_id', 'amount', 'time_since_last_txn', 'avg_amount_7d', 'txns_last_1h', 'location_changed']].head())

if __name__ == "__main__":
    preprocess_data()
