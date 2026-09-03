"""
Model Training Script for Telemetry Anomaly Detector & Root-Cause Classifier
Trains:
1. Unsupervised IsolationForest for real-time anomaly score computation.
2. Supervised Anomaly Classifier (Random Forest) for precise failure pattern identification.
Outputs: backend/models/telemetry_anomaly.joblib
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

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

def train_telemetry_models():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(backend_dir, 'datasets', 'telemetry_train.csv')
    models_dir = os.path.join(backend_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    # Ensure dataset exists
    if not os.path.exists(dataset_path):
        from datasets.generate_telemetry_dataset import generate_telemetry_dataset
        print("Generating telemetry dataset...")
        df = generate_telemetry_dataset(num_samples=8000)
        os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
        df.to_csv(dataset_path, index=False)
    else:
        df = pd.read_csv(dataset_path)
        
    print(f"Loaded {len(df)} samples for telemetry training.")
    
    X = df[FEATURE_COLS].values
    y_anomaly = df['is_anomaly'].values
    y_type = df['anomaly_type'].values
    
    # Train-test split
    X_train, X_test, y_ano_train, y_ano_test, y_type_train, y_type_test = train_test_split(
        X, y_anomaly, y_type, test_size=0.2, random_state=42, stratify=y_type
    )
    
    # 1. Feature Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 2. Isolation Forest (Unsupervised Anomaly Detector)
    print("Training Isolation Forest Anomaly Detector...")
    # Train on normal + subset to learn normal distribution boundary
    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=0.20,
        max_samples=0.85,
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_train_scaled)
    
    # Evaluate Isolation Forest
    # In IsolationForest, -1 is anomaly, 1 is normal
    raw_scores = iso_forest.score_samples(X_test_scaled)
    # Convert raw anomaly score to continuous [0, 1] probability (higher = more anomalous)
    anomaly_probs = 1.0 / (1.0 + np.exp(raw_scores * 8.0))
    auc_score = roc_auc_score(y_ano_test, anomaly_probs)
    print(f"Isolation Forest ROC-AUC Score: {auc_score:.4f}")
    
    # 3. Supervised Multi-Class Anomaly Type Classifier
    print("Training Multi-Class Anomaly Root Cause Classifier...")
    classifier = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    classifier.fit(X_train_scaled, y_type_train)
    
    y_pred_type = classifier.predict(X_test_scaled)
    print("\nClassification Report (Anomaly Diagnosis Types):")
    print(classification_report(y_type_test, y_pred_type))
    
    # Save model bundle
    bundle = {
        'feature_cols': FEATURE_COLS,
        'scaler': scaler,
        'isolation_forest': iso_forest,
        'classifier': classifier,
        'classes': list(classifier.classes_)
    }
    
    model_save_path = os.path.join(models_dir, 'telemetry_anomaly.joblib')
    joblib.dump(bundle, model_save_path)
    print(f"\nSaved trained telemetry ML pipeline to -> {model_save_path}")
    return bundle

if __name__ == '__main__':
    train_telemetry_models()
