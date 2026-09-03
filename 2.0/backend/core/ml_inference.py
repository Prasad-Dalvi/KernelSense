"""
Machine Learning Inference Engine for KernelSense
Performs real-time scoring and classification using trained serialized models:
- Telemetry Anomaly Detector (IsolationForest + Multi-Class Root Cause Classifier)
- NLP Log Classifier (TF-IDF + Random Forest)
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, Optional

FEATURE_COLS = [
    'cpu_percent',
    'cpu_variance',
    'mem_percent',
    'mem_slope',
    'swap_percent',
    'disk_read_mbs',
    'disk_write_mbs',
    'net_sent_mbs',
    'net_recv_mbs',
    'context_switches',
    'num_threads'
]

class MLEngine:
    def __init__(self):
        self.backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.models_dir = os.path.join(self.backend_dir, 'models')
        self.telemetry_bundle: Optional[Dict[str, Any]] = None
        self.log_bundle: Optional[Dict[str, Any]] = None
        self.load_models()
        
    def load_models(self):
        telemetry_path = os.path.join(self.models_dir, 'telemetry_anomaly.joblib')
        log_path = os.path.join(self.models_dir, 'log_classifier.joblib')
        
        if os.path.exists(telemetry_path):
            try:
                self.telemetry_bundle = joblib.load(telemetry_path)
            except Exception as e:
                print(f"[ML Engine] Failed to load telemetry model: {e}")
                
        if os.path.exists(log_path):
            try:
                self.log_bundle = joblib.load(log_path)
            except Exception as e:
                print(f"[ML Engine] Failed to load log model: {e}")

    def predict_telemetry_anomaly(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Runs real-time anomaly detection on multi-variate OS metrics.
        Returns continuous anomaly score [0.0 - 1.0], anomaly flag, root cause class, and top factors.
        """
        if not self.telemetry_bundle:
            # Fallback if model hasn't been loaded
            self.load_models()
            if not self.telemetry_bundle:
                return {
                    "is_anomaly": False,
                    "anomaly_score": 0.1,
                    "anomaly_type": "NORMAL",
                    "confidence": 0.9,
                    "contributing_factors": []
                }
                
        scaler = self.telemetry_bundle['scaler']
        iso_forest = self.telemetry_bundle['isolation_forest']
        classifier = self.telemetry_bundle['classifier']
        
        # Build feature vector
        vector = []
        for col in FEATURE_COLS:
            vector.append(float(metrics.get(col, 0.0)))
            
        X = np.array([vector])
        X_scaled = scaler.transform(X)
        
        # Calculate continuous probability from Isolation Forest decision function
        # decision_function is positive for inliers (> 0) and negative for outliers (< 0)
        decision_score = iso_forest.decision_function(X_scaled)[0]
        # Sigmoid: decision_score > 0 -> prob < 0.5; decision_score < 0 -> prob > 0.5
        prob = float(1.0 / (1.0 + np.exp(decision_score * 12.0)))
        is_anomaly = bool(prob >= 0.50 or decision_score < 0.0)
        
        # Predict type
        pred_type = classifier.predict(X_scaled)[0]
        probas = classifier.predict_proba(X_scaled)[0]
        max_idx = int(np.argmax(probas))
        confidence = float(probas[max_idx])
        
        # If model says NORMAL or probability is low
        if not is_anomaly:
            pred_type = "NORMAL"
            
        # Determine top contributing features
        # Compute deviation from scaled mean
        deviations = np.abs(X_scaled[0])
        top_indices = np.argsort(deviations)[::-1][:3]
        factors = [
            {
                "feature": FEATURE_COLS[i],
                "value": vector[i],
                "z_score": float(deviations[i])
            }
            for i in top_indices if deviations[i] > 1.2
        ]
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(prob, 3),
            "anomaly_type": pred_type,
            "confidence": round(confidence, 3),
            "contributing_factors": factors
        }

    def predict_log(self, message: str) -> Dict[str, Any]:
        """
        Classifies a system log line into error/crash categories and returns severity.
        """
        if not self.log_bundle:
            self.load_models()
            if not self.log_bundle:
                return {
                    "category": "NORMAL_INFO",
                    "severity": "info",
                    "confidence": 0.85
                }
                
        vectorizer = self.log_bundle['vectorizer']
        model = self.log_bundle['model']
        
        vec = vectorizer.transform([message])
        pred_cat = model.predict(vec)[0]
        probas = model.predict_proba(vec)[0]
        max_idx = int(np.argmax(probas))
        confidence = float(probas[max_idx])
        
        # Map category to UI severity
        severity_map = {
            'OOM_KILLER': 'error',
            'KERNEL_PANIC': 'error',
            'IO_ERROR': 'error',
            'NETWORK_FAILURE': 'warning',
            'SECURITY_ALERT': 'warning',
            'NORMAL_INFO': 'info'
        }
        severity = severity_map.get(pred_cat, 'info')
        
        return {
            "category": pred_cat,
            "severity": severity,
            "confidence": round(confidence, 3)
        }

# Global singleton
ml_engine = MLEngine()
