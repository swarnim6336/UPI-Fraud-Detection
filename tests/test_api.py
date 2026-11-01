import pytest
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.index import app

client = TestClient(app)

def test_health_endpoint():
    """Verify the /health endpoint reports models loaded and ready."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["models_loaded"] is True
    assert data["features_count"] > 0

def test_frontend_served():
    """Verify that root endpoint serves the index.html dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

def test_predict_endpoint_valid():
    """Verify that a valid transaction payload returns a complete fraud assessment."""
    payload = {
        "user_id": "U1001",
        "amount": 2500.0,
        "merchant_category": "electronics",
        "device_id": "DEV_9918",
        "location": "Lucknow"
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "status" in data
    assert "reasons" in data
    assert "feature_vector" in data
    assert 0 <= data["score"] <= 100
    assert data["status"] in ["APPROVED", "WARNING", "CRITICAL"]

def test_predict_endpoint_validation_error():
    """Invalid payload schema should return 422 Unprocessable Entity."""
    payload = {
        "user_id": "U1001",
        "amount": "not-a-number",  # Invalid type
        "merchant_category": "groceries"
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422
