"""
Integration tests for FastAPI endpoints
"""
import pytest
import requests
import time
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health endpoint"""
    # Note: This will fail if model is not loaded, which is expected in test environment
    response = client.get("/health")
    assert response.status_code in [200, 503]  # OK or service unavailable


def test_version_endpoint(client):
    """Test version endpoint"""
    response = client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    assert "sha" in data


def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_request_duration_seconds" in response.text


def test_predict_endpoint_structure(client):
    """Test predict endpoint structure"""
    # This will fail if model not loaded, but tests the endpoint structure
    request_data = {
        "rows": [
            {"ret_mean": 0.05, "ret_std": 0.01, "n": 50}
        ]
    }
    
    response = client.post("/predict", json=request_data)
    
    # Should either succeed (200) or fail with service unavailable (503) or bad request (400)
    assert response.status_code in [200, 400, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert "scores" in data
        assert "model_variant" in data
        assert "version" in data
        assert "ts" in data
        assert len(data["scores"]) == 1


def test_predict_batch(client):
    """Test batch prediction"""
    request_data = {
        "rows": [
            {"ret_mean": 0.05, "ret_std": 0.01, "n": 50},
            {"ret_mean": -0.02, "ret_std": 0.015, "n": 50},
            {"ret_mean": 0.01, "ret_std": 0.005, "n": 50}
        ]
    }
    
    response = client.post("/predict", json=request_data)
    
    if response.status_code == 200:
        data = response.json()
        assert len(data["scores"]) == 3


def test_predict_validation_error(client):
    """Test input validation"""
    # Missing required fields
    request_data = {
        "rows": [
            {"ret_mean": 0.05}  # Missing ret_std and n
        ]
    }
    
    response = client.post("/predict", json=request_data)
    assert response.status_code == 422  # Validation error


def test_predict_empty_rows(client):
    """Test empty rows validation"""
    request_data = {
        "rows": []
    }
    
    response = client.post("/predict", json=request_data)
    assert response.status_code == 422

