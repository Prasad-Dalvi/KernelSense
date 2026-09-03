"""
Comprehensive Model Evaluation Script for KernelSense
Evaluates:
1. Telemetry Anomaly Detector on real-time simulated metric spikes
2. NLP Log Classifier on unseen kernel & failure messages
Outputs benchmark summaries and validation confidence scores.
"""

import os
import joblib
import numpy as np

def run_benchmarks():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(backend_dir, 'models')
    
    telemetry_model_path = os.path.join(models_dir, 'telemetry_anomaly.joblib')
    log_model_path = os.path.join(models_dir, 'log_classifier.joblib')
    
    if not os.path.exists(telemetry_model_path) or not os.path.exists(log_model_path):
        print("Models not found yet. Run training scripts first.")
        return
        
    print("=" * 60)
    print(" [BENCHMARK] KERNELSENSE MACHINE LEARNING MODEL BENCHMARK & TEST")
    print("=" * 60)
    
    # 1. Evaluate Telemetry Anomaly Detector
    print("\n--- [1] Telemetry ML Anomaly Inference Verification ---")
    tele_bundle = joblib.load(telemetry_model_path)
    scaler = tele_bundle['scaler']
    iso_forest = tele_bundle['isolation_forest']
    classifier = tele_bundle['classifier']
    
    test_telemetry_vectors = {
        "Normal Idle Server": [12.5, 1.2, 45.0, 0.0, 5.0, 2.1, 4.5, 0.8, 1.2, 2200, 1100],
        "Extreme Memory Leak": [35.0, 3.5, 96.8, 2.8, 88.5, 15.0, 65.0, 2.0, 4.0, 8500, 1800],
        "CPU Infinite Loop Thrash": [99.5, 0.2, 52.0, 0.0, 2.0, 0.5, 1.0, 0.2, 0.5, 32000, 1400],
        "Disk I/O Choke": [28.0, 2.0, 62.0, 0.0, 12.0, 380.0, 420.0, 1.5, 2.0, 18000, 1300],
        "DDoS / Network Inundation": [68.0, 8.0, 48.0, 0.0, 0.0, 5.0, 8.0, 180.0, 350.0, 22000, 2100],
    }
    
    for label, vec in test_telemetry_vectors.items():
        scaled = scaler.transform([vec])
        decision_score = iso_forest.decision_function(scaled)[0]
        # Anomaly probability [0, 1]
        prob = float(1.0 / (1.0 + np.exp(decision_score * 12.0)))
        pred_type = classifier.predict(scaled)[0]
        confidence = float(np.max(classifier.predict_proba(scaled)))
        
        status = "ANOMALY DETECTED" if prob >= 0.50 else "HEALTHY (NORMAL)"
        print(f"[{status:17}] {label:28} | Anomaly Score: {prob*100:5.1f}% | Predicted Class: {pred_type:18} ({confidence*100:.1f}% conf)")
        
    # 2. Evaluate NLP Log Classifier
    print("\n--- [2] NLP Log Threat & Failure Inference Verification ---")
    log_bundle = joblib.load(log_model_path)
    vectorizer = log_bundle['vectorizer']
    log_model = log_bundle['model']
    
    test_log_lines = [
        "kernel: [ 1042.88 ] Out of memory: Kill process 1892 (mysqld) score 850 or sacrifice child",
        "kernel: [ 3120.12 ] BUG: unable to handle page fault for address: 0x0000000000000010",
        "kernel: [ 451.90 ] EXT4-fs error (device sda1): ext4_lookup: deleted inode referenced: 4192",
        "sshd[4102]: Failed password for invalid user admin from 192.168.1.105 port 58212 ssh2",
        "kernel: [ 89.23 ] eth0: link down, carrier lost",
        "systemd[1]: Started Service for user session 1000.",
    ]
    
    for line in test_log_lines:
        vec = vectorizer.transform([line])
        cat = log_model.predict(vec)[0]
        proba = float(np.max(log_model.predict_proba(vec)))
        print(f"-> Log: \"{line[:65]}...\"\n   Category: [{cat}] ({proba*100:.1f}% confidence)\n")

if __name__ == '__main__':
    run_benchmarks()
