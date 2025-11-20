"""
Feature engineering with sliding window
"""
import numpy as np
from collections import deque
from typing import Optional, Dict, Any


class FeatureEngine:
    """Sliding window feature engineering"""
    
    def __init__(self, window_size: int = 50):
        """
        Initialize feature engine
        
        Args:
            window_size: Size of sliding window
        """
        self.window_size = window_size
        self.prices = deque(maxlen=window_size)
        self.returns = deque(maxlen=window_size - 1)
    
    def update(self, price: float) -> Optional[Dict[str, float]]:
        """
        Update with new price and compute features
        
        Args:
            price: Current price
        
        Returns:
            Dict with ret_mean, ret_std, n if window is ready, None otherwise
        """
        self.prices.append(price)
        
        # Calculate returns if we have at least 2 prices
        if len(self.prices) >= 2:
            prev_price = self.prices[-2]
            if prev_price > 0:
                ret = (price - prev_price) / prev_price
                self.returns.append(ret)
        
        # Check if we have enough data
        if len(self.returns) < self.window_size - 1:
            return None
        
        # Compute features
        returns_array = np.array(self.returns)
        
        ret_mean = float(np.mean(returns_array))
        ret_std = float(np.std(returns_array))
        n = len(returns_array)
        
        return {
            "ret_mean": ret_mean,
            "ret_std": ret_std if ret_std > 0 else 1e-8,  # Avoid division by zero
            "n": n
        }
    
    def reset(self):
        """Reset the feature engine"""
        self.prices.clear()
        self.returns.clear()

