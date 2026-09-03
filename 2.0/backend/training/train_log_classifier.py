"""
Model Training Script for NLP System Log Classifier
Trains TF-IDF Vectorizer + Random Forest Classifier on Linux Kernel and System Logs.
Outputs: backend/models/log_classifier.joblib
"""

import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def train_log_classifier():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(backend_dir, 'datasets', 'logs_train.csv')
    models_dir = os.path.join(backend_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    if not os.path.exists(dataset_path):
        from datasets.generate_log_dataset import generate_log_dataset
        print("Generating log dataset...")
        df = generate_log_dataset(samples_per_category=700)
        os.makedirs(os.path.dirname(dataset_path), exist_ok=True)
        df.to_csv(dataset_path, index=False)
    else:
        df = pd.read_csv(dataset_path)
        
    print(f"Loaded {len(df)} log samples for NLP training.")
    
    X_text = df['message'].values
    y_category = df['category'].values
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_text, y_category, test_size=0.2, random_state=42, stratify=y_category
    )
    
    print("Fitting TF-IDF N-gram Vectorizer...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=6000,
        sublinear_tf=True,
        token_pattern=r'(?u)\b\w+\b'
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    print("Training Random Forest NLP Log Classifier...")
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=20,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_vec, y_train)
    
    y_pred = model.predict(X_test_vec)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nOverall Log Classification Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report (NLP System Logs):")
    print(classification_report(y_test, y_pred))
    
    bundle = {
        'vectorizer': vectorizer,
        'model': model,
        'classes': list(model.classes_)
    }
    
    model_save_path = os.path.join(models_dir, 'log_classifier.joblib')
    joblib.dump(bundle, model_save_path)
    print(f"\nSaved trained NLP Log Pipeline to -> {model_save_path}")
    return bundle

if __name__ == '__main__':
    train_log_classifier()
