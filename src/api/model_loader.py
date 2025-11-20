"""
Model loader with MLflow integration
"""
import os
import logging
from typing import List, Optional
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)


class ModelLoader:
    """Loads and manages ML models with MLflow support"""
    
    def __init__(self):
        self.model = None
        self.model_variant = os.getenv("MODEL_VARIANT", "ml")
        self.model_name = os.getenv("MODEL_NAME", "crypto_volatility_model")
        self.model_version = os.getenv("MODEL_VERSION", "latest")
        self.mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
        self.loaded_version = None
        
        # Set MLflow tracking URI
        mlflow.set_tracking_uri(self.mlflow_uri)
    
    async def load_model(self):
        """Load model from MLflow or create baseline"""
        try:
            if self.model_variant == "baseline":
                self._load_baseline_model()
            else:
                self._load_mlflow_model()
            
            logger.info(f"Model loaded: variant={self.model_variant}, version={self.loaded_version}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Fallback to baseline
            logger.warning("Falling back to baseline model")
            self.model_variant = "baseline"
            self._load_baseline_model()
    
    def _load_mlflow_model(self):
        """Load model from MLflow"""
        try:
            client = mlflow.tracking.MlflowClient(tracking_uri=self.mlflow_uri)
            
            # Try to get the model
            if self.model_version == "latest":
                model_versions = client.search_model_versions(f"name='{self.model_name}'")
                if model_versions:
                    latest = max(model_versions, key=lambda x: x.version)
                    model_uri = f"models:/{self.model_name}/{latest.version}"
                    self.loaded_version = latest.version
                else:
                    raise ValueError(f"No model versions found for {self.model_name}")
            else:
                model_uri = f"models:/{self.model_name}/{self.model_version}"
                self.loaded_version = self.model_version
            
            # Load the model
            self.model = mlflow.sklearn.load_model(model_uri)
            logger.info(f"Loaded MLflow model: {model_uri}")
            
        except Exception as e:
            logger.error(f"MLflow model loading failed: {e}")
            raise
    
    def _load_baseline_model(self):
        """Load or create baseline model"""
        # Simple baseline: Logistic Regression with default params
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        
        # Train on dummy data (in production, this would be pre-trained)
        # For now, we'll use a simple rule-based approach
        # This is a placeholder - in real implementation, you'd load a pre-trained baseline
        X_dummy = np.array([[0.01, 0.005, 50], [0.05, 0.02, 50], [-0.01, 0.005, 50]])
        y_dummy = np.array([0, 1, 0])  # Binary classification: 0=low vol, 1=high vol
        self.model.fit(X_dummy, y_dummy)
        
        self.loaded_version = "baseline_v1"
        logger.info("Loaded baseline model")
    
    def predict(self, features: List[List[float]]) -> np.ndarray:
        """
        Make predictions on features
        
        Args:
            features: List of feature vectors [ret_mean, ret_std, n]
        
        Returns:
            Array of prediction scores
        """
        if self.model is None:
            raise ValueError("Model not loaded")
        
        X = np.array(features)
        
        # Handle different model types
        if hasattr(self.model, 'predict_proba'):
            # Classification model
            predictions = self.model.predict_proba(X)[:, 1]  # Probability of positive class
        else:
            # Regression model
            predictions = self.model.predict(X)
        
        return predictions
    
    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None
    
    def get_variant(self) -> str:
        """Get current model variant"""
        return self.model_variant
    
    def get_version(self) -> str:
        """Get current model version"""
        return self.loaded_version or "unknown"

