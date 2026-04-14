"""
ML-based Anomaly Detection Module
Uses Isolation Forest for unsupervised anomaly detection.
Works alongside rule-based detection for hybrid approach.
"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
import config

# Try to import sklearn, but make it optional
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("WARNING: scikit-learn not installed. ML detection disabled.")


class MLDetector:
    """
    Machine Learning based anomaly detector using Isolation Forest.
    Provides explainable anomaly detection for system metrics.
    """
    
    def __init__(self, contamination=0.1, n_estimators=100):
        """
        Initialize ML detector.
        
        Args:
            contamination: Expected proportion of anomalies (0.0-0.5)
            n_estimators: Number of isolation trees
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        
        # Model and scaler
        self.model = None
        self.scaler = None
        
        if SKLEARN_AVAILABLE:
            self.scaler = StandardScaler()
        
        # Training data
        self.feature_history = []
        self.min_samples_for_training = 60  # Minimum 60 samples (1 minute of data)
        
        # Feature names for explainability
        self.feature_names = ['cpu_usage', 'memory_usage', 'disk_usage', 
                             'cpu_std', 'memory_std', 'process_count']
        
        # Logger
        self.logger = logging.getLogger('SystemObserver.ML')
        
        # Training status
        self.is_trained = False
        self.last_training_time = None
        
        # Results cache
        self.last_prediction = None
        self.last_score = None
    
    def add_sample(self, cpu_usage: float, memory_usage: float, disk_usage: float,
                   process_count: int, cpu_std: float = 0, memory_std: float = 0):
        """
        Add a data sample for training/prediction.
        
        Args:
            cpu_usage: Current CPU usage percentage
            memory_usage: Current memory usage percentage
            disk_usage: Current disk usage percentage
            process_count: Number of running processes
            cpu_std: Standard deviation of CPU (from rolling window)
            memory_std: Standard deviation of memory (from rolling window)
        """
        features = [
            cpu_usage,
            memory_usage,
            disk_usage,
            cpu_std,
            memory_std,
            process_count / 100.0  # Normalize process count
        ]
        
        self.feature_history.append({
            'timestamp': datetime.now(),
            'features': features
        })
        
        # Keep only last 10000 samples max
        max_samples = 10000
        if len(self.feature_history) > max_samples:
            self.feature_history = self.feature_history[-max_samples:]
    
    def should_train(self) -> bool:
        """
        Check if we have enough data to train the model.
        
        Returns:
            bool: True if we should train the model
        """
        if not SKLEARN_AVAILABLE:
            return False
        return len(self.feature_history) >= self.min_samples_for_training and not self.is_trained
    
    def can_predict(self) -> bool:
        """
        Check if model can make predictions.
        
        Returns:
            bool: True if model is ready for predictions
        """
        return SKLEARN_AVAILABLE and self.is_trained and self.model is not None
    
    def train(self) -> bool:
        """
        Train the Isolation Forest model on historical data.
        
        Returns:
            bool: True if training succeeded
        """
        if not SKLEARN_AVAILABLE:
            self.logger.warning("scikit-learn not available. ML training skipped.")
            return False
        
        if len(self.feature_history) < self.min_samples_for_training:
            self.logger.warning(f"Not enough samples for training: {len(self.feature_history)}/{self.min_samples_for_training}")
            return False
        
        try:
            # Extract features
            X = np.array([sample['features'] for sample in self.feature_history])
            
            # Handle any NaN or Inf values
            X = np.nan_to_num(X, nan=0.0, posinf=100.0, neginf=0.0)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Isolation Forest
            self.model = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_scaled)
            
            self.is_trained = True
            self.last_training_time = datetime.now()
            
            self.logger.info(f"ML model trained successfully with {len(X)} samples")
            return True
            
        except Exception as e:
            self.logger.error(f"Error training ML model: {e}")
            return False
    
    def retrain(self) -> bool:
        """
        Retrain the model with updated data.
        
        Returns:
            bool: True if retraining succeeded
        """
        self.is_trained = False
        self.model = None
        return self.train()
    
    def predict(self, cpu_usage: float, memory_usage: float, disk_usage: float,
                process_count: int, cpu_std: float = 0, memory_std: float = 0) -> Tuple[bool, float, str]:
        """
        Predict if current metrics are anomalous.
        
        Args:
            cpu_usage: Current CPU usage percentage
            memory_usage: Current memory usage percentage
            disk_usage: Current disk usage percentage
            process_count: Number of running processes
            cpu_std: Standard deviation of CPU
            memory_std: Standard deviation of memory
            
        Returns:
            Tuple of (is_anomaly, anomaly_score, explanation)
        """
        if not SKLEARN_AVAILABLE:
            return False, 0.0, "ML not available"
        
        if not self.can_predict():
            return False, 0.0, "ML model not trained"
        
        try:
            # Prepare features
            features = np.array([[
                cpu_usage,
                memory_usage,
                disk_usage,
                cpu_std,
                memory_std,
                process_count / 100.0
            ]])
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get prediction (-1 for anomaly, 1 for normal)
            prediction = self.model.predict(features_scaled)[0]
            
            # Get anomaly score (more negative = more anomalous)
            anomaly_score = self.model.score_samples(features_scaled)[0]
            
            # Convert to 0-100 scale (higher = more anomalous)
            anomaly_score_normalized = (0.5 - anomaly_score) * 200
            anomaly_score_normalized = max(0, min(100, anomaly_score_normalized))
            
            is_anomaly = prediction == -1
            
            # Generate explanation
            explanation = self._generate_explanation(
                cpu_usage, memory_usage, disk_usage, anomaly_score_normalized
            )
            
            self.last_prediction = is_anomaly
            self.last_score = anomaly_score_normalized
            
            return is_anomaly, anomaly_score_normalized, explanation
            
        except Exception as e:
            self.logger.error(f"Error in ML prediction: {e}")
            return False, 0.0, f"Prediction error: {str(e)}"
    
    def _generate_explanation(self, cpu: float, memory: float, disk: float, 
                              score: float) -> str:
        """
        Generate human-readable explanation for anomaly.
        
        Args:
            cpu: CPU usage
            memory: Memory usage
            disk: Disk usage
            score: Anomaly score
            
        Returns:
            str: Explanation string
        """
        # Find which features are contributing most to the anomaly
        contributing_factors = []
        
        # Typical baseline values
        baseline_cpu = 30
        baseline_memory = 50
        baseline_disk = 70
        
        if cpu > baseline_cpu + 20:
            contributing_factors.append(f"CPU ({cpu:.1f}%)")
        
        if memory > baseline_memory + 15:
            contributing_factors.append(f"Memory ({memory:.1f}%)")
        
        if disk > baseline_disk + 10:
            contributing_factors.append(f"Disk ({disk:.1f}%)")
        
        if contributing_factors:
            return f"Unusual pattern detected in: {', '.join(contributing_factors)}"
        else:
            return f"Statistical anomaly detected (score: {score:.1f})"
    
    def get_training_stats(self) -> Dict:
        """
        Get training statistics.
        
        Returns:
            Dict with training info
        """
        return {
            'sample_count': len(self.feature_history),
            'min_samples_required': self.min_samples_for_training,
            'is_trained': self.is_trained,
            'sklearn_available': SKLEARN_AVAILABLE,
            'last_training_time': self.last_training_time.isoformat() if self.last_training_time else None,
            'contamination': self.contamination,
            'n_estimators': self.n_estimators
        }
    
    def reset(self):
        """
        Reset the detector - clears all data and model.
        """
        self.feature_history = []
        self.model = None
        if self.scaler:
            self.scaler = StandardScaler()
        self.is_trained = False
        self.last_training_time = None
        self.last_prediction = None
        self.last_score = None
        self.logger.info("ML detector reset")


# Module-level instance
_ml_detector = None


def get_ml_detector() -> MLDetector:
    """
    Get the singleton ML detector instance.
    
    Returns:
        MLDetector instance
    """
    global _ml_detector
    if _ml_detector is None:
        _ml_detector = MLDetector()
    return _ml_detector
