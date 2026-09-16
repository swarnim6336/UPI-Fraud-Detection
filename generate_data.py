import pandas as pd
import numpy as np
import uuid
import random
from datetime import datetime, timedelta

def generate_data(num_records=10000):
    # Set seed for reproducibility
    np.random.seed(42)
    random.seed(42)
    
    users = [f"user_{i}" for i in range(1, 101)] # 100 users
    receivers = [f"merchant_{i}" for i in range(1, 201)] + [f"unknown_receiver_{i}" for i in range(1, 51)]
    categories = ['Grocery', 'Rent', 'Utilities', 'Electronics', 'Entertainment', 'Transfer', 'Unknown']
    locations = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata']
    
    # User profiles: assign a primary location and primary device to each user
    user_profiles = {}
    for user in users:
        user_profiles[user] = {
            'home_location': random.choice(locations),
            'primary_device': f"device_{uuid.uuid4().hex[:8]}",
            'avg_txn_value': random.uniform(100, 1000) # Base avg transaction for this user
        }
    
    data = []
    
    # Generate dates over a 30-day period
    start_date = datetime.now() - timedelta(days=30)
    
    for _ in range(num_records):
        is_fraud = False
        user = random.choice(users)
        profile = user_profiles[user]
        
        # Decide if this transaction is normal or fraud (approx 5% fraud)
        if random.random() < 0.05:
            is_fraud = True
            
        if not is_fraud:
            # Normal behavior
            amount = max(10, np.random.normal(profile['avg_txn_value'], profile['avg_txn_value'] * 0.5))
            
            # Rent is usually high but once a month
            if random.random() < 0.05:
                category = 'Rent'
                amount = random.uniform(10000, 30000)
            else:
                category = random.choice(['Grocery', 'Utilities', 'Entertainment', 'Transfer'])
                
            receiver = random.choice([r for r in receivers if 'merchant' in r])
            location = profile['home_location']
            device = profile['primary_device']
            
            # Normal hours: 7 AM to 10 PM
            hour = random.randint(7, 22)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            day_offset = random.randint(0, 29)
            txn_date = start_date + timedelta(days=day_offset)
            txn_time = txn_date.replace(hour=hour, minute=minute, second=second)
            
        else:
            # Fraud behavior
            fraud_type = random.choice(['spike', 'location_spoof', 'late_night'])
            
            if fraud_type == 'spike':
                # Massive spike in amount
                amount = profile['avg_txn_value'] * random.uniform(10, 50)
                category = 'Electronics'
                location = profile['home_location']
                device = profile['primary_device']
                hour = random.randint(7, 22)
                receiver = random.choice([r for r in receivers if 'unknown' in r])
                
            elif fraud_type == 'location_spoof':
                # Location spoofing + new device
                amount = random.uniform(5000, 20000)
                category = 'Transfer'
                location = random.choice([loc for loc in locations if loc != profile['home_location']])
                device = f"device_{uuid.uuid4().hex[:8]}" # New device
                hour = random.randint(7, 22)
                receiver = random.choice(receivers)
                
            else: # late_night
                # Late night transaction to unknown receiver
                amount = random.uniform(1000, 5000)
                category = 'Unknown'
                location = profile['home_location']
                device = profile['primary_device']
                hour = random.choice([23, 0, 1, 2, 3, 4]) # Late night
                receiver = random.choice([r for r in receivers if 'unknown' in r])
                
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            day_offset = random.randint(0, 29)
            txn_date = start_date + timedelta(days=day_offset)
            txn_time = txn_date.replace(hour=hour, minute=minute, second=second)

        data.append({
            'transaction_id': str(uuid.uuid4()),
            'user_id': user,
            'receiver_id': receiver,
            'amount': round(amount, 2),
            'timestamp': txn_time,
            'merchant_category': category,
            'device_id': device,
            'location': location,
            'is_fraud': int(is_fraud)
        })

    df = pd.DataFrame(data)
    # Sort by timestamp to simulate realistic streaming/time-series data
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Save to CSV
    output_path = 'upi_transactions.csv'
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} transactions and saved to {output_path}")
    print(f"Fraud distribution:\n{df['is_fraud'].value_counts(normalize=True) * 100}")

if __name__ == "__main__":
    generate_data(10000)
