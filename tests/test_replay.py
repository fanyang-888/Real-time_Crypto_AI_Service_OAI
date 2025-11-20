"""
Tests for data replay functionality
"""
import pytest
import pandas as pd
import os
import tempfile

from src.ingestion.producer import CoinbaseIngestor
from src.features.feature_engineering import FeatureEngine


def test_feature_engine():
    """Test feature engineering"""
    engine = FeatureEngine(window_size=5)
    
    # Add prices
    prices = [100.0, 101.0, 102.0, 101.5, 103.0, 104.0]
    
    features_list = []
    for price in prices:
        features = engine.update(price)
        if features is not None:
            features_list.append(features)
    
    # Should have features after window is filled
    assert len(features_list) > 0
    
    # Check feature structure
    if features_list:
        feat = features_list[0]
        assert "ret_mean" in feat
        assert "ret_std" in feat
        assert "n" in feat
        assert feat["n"] > 0


def test_feature_engine_window():
    """Test sliding window behavior"""
    engine = FeatureEngine(window_size=3)
    
    # Add exactly window_size prices
    engine.update(100.0)
    engine.update(101.0)
    engine.update(102.0)
    
    # Should not have features yet (need window_size - 1 returns)
    features = engine.update(103.0)
    assert features is not None
    assert features["n"] == 3  # 3 returns


def test_ingestor_data_loading():
    """Test data loading functionality"""
    # Create sample data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("timestamp,price,volume\n")
        f.write("2025-01-01 10:00:00,100.0,1000\n")
        f.write("2025-01-01 10:01:00,101.0,1100\n")
        f.write("2025-01-01 10:02:00,102.0,1200\n")
        temp_file = f.name
    
    try:
        ingestor = CoinbaseIngestor()
        ingestor.data_file = temp_file
        
        df = ingestor.load_data()
        assert len(df) == 3
        assert "price" in df.columns
    finally:
        os.unlink(temp_file)

