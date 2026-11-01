import pytest
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scoring import calculate_fraud_score, iqr_df, zscore_params

def test_artifacts_loaded():
    """Verify core statistical and ML artifacts are loaded."""
    assert iqr_df is not None
    assert not iqr_df.empty, "IQR thresholds should not be empty"
    assert "velocity_mean" in zscore_params
    assert "velocity_std" in zscore_params

def test_normal_transaction():
    """A standard low-amount transaction with normal velocity should be approved."""
    known_user = iqr_df.index[0]
    features = {
        'amount': 150.0,
        'time_since_last_txn': 86400,
        'avg_amount_7d': 200.0,
        'txns_last_1h': 0,
        'location_changed': 0,
        'device_changed': 0
    }
    result = calculate_fraud_score(known_user, 150.0, features)
    assert "score" in result
    assert "status" in result
    assert "reasons" in result
    assert 0 <= result["score"] <= 100

def test_iqr_threshold_breach():
    """An amount exceeding the user's historical IQR upper bound triggers a score penalty."""
    known_user = iqr_df.index[0]
    upper_bound = iqr_df.loc[known_user, 'Upper_Bound']
    breach_amount = upper_bound + 50000.0
    
    features = {
        'amount': breach_amount,
        'time_since_last_txn': 3600,
        'avg_amount_7d': upper_bound / 2,
        'txns_last_1h': 1,
        'location_changed': 0,
        'device_changed': 0
    }
    result = calculate_fraud_score(known_user, breach_amount, features)
    assert result["score"] >= 40
    assert any("exceeds historical normal limits" in r for r in result["reasons"])

def test_velocity_zscore_breach():
    """High transaction velocity with Z-score > 2.0 triggers a velocity penalty."""
    known_user = iqr_df.index[0]
    features = {
        'amount': 200.0,
        'time_since_last_txn': 5,
        'avg_amount_7d': 200.0,
        'txns_last_1h': 50,  # Extreme velocity
        'location_changed': 0,
        'device_changed': 0
    }
    result = calculate_fraud_score(known_user, 200.0, features)
    assert any("Unusual transaction velocity" in r for r in result["reasons"])

def test_score_bounded_at_100():
    """Even if all rules fire, the score should never exceed 100."""
    known_user = iqr_df.index[0]
    features = {
        'amount': 9999999.0,
        'time_since_last_txn': 1,
        'avg_amount_7d': 10.0,
        'txns_last_1h': 100,
        'location_changed': 1,
        'device_changed': 1
    }
    result = calculate_fraud_score(known_user, 9999999.0, features)
    assert result["score"] <= 100
    assert result["status"] == "CRITICAL"
