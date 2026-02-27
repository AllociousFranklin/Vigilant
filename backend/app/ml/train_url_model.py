"""VIGILANT ML - URL Classifier Training Script

Trains an XGBoost classifier on phishing URL features.
Uses a synthetic dataset augmented with real-world patterns.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from xgboost import XGBClassifier
import joblib

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import hashlib
from app.engine.features import extract_url_features, extract_nlp_features, extract_structural_features
from app.engine.detector import ALL_FEATURE_NAMES, get_feature_fingerprint


def generate_training_data(n_samples=5000):
    """Generate synthetic training data based on real-world phishing patterns."""
    np.random.seed(42)
    data = []
    
    # === PHISHING URLs (label=1) ===
    n_phishing = n_samples // 2
    for i in range(n_phishing):
        pattern = np.random.choice(['brand_spoof', 'ip_based', 'long_random', 'suspicious_tld', 'encoded'])
        
        features = {}
        
        if pattern == 'brand_spoof':
            features['url_length'] = np.random.randint(40, 120)
            features['url_dot_count'] = np.random.randint(3, 7)
            features['url_hyphen_count'] = np.random.randint(1, 5)
            features['url_at_symbol'] = np.random.choice([0, 1], p=[0.8, 0.2])
            features['url_entropy'] = np.random.uniform(3.5, 5.5)
            features['url_digit_ratio'] = np.random.uniform(0.05, 0.3)
            features['url_has_ip'] = 0
            features['url_suspicious_tld'] = np.random.choice([0, 1], p=[0.5, 0.5])
            features['url_subdomain_depth'] = np.random.randint(1, 4)
            features['url_path_length'] = np.random.randint(10, 60)
            features['url_has_https'] = np.random.choice([0, 1], p=[0.4, 0.6])
            features['url_brand_similarity'] = np.random.uniform(0.5, 0.95)
            
        elif pattern == 'ip_based':
            features['url_length'] = np.random.randint(20, 80)
            features['url_dot_count'] = np.random.randint(3, 6)
            features['url_hyphen_count'] = np.random.randint(0, 2)
            features['url_at_symbol'] = 0
            features['url_entropy'] = np.random.uniform(3.0, 4.5)
            features['url_digit_ratio'] = np.random.uniform(0.2, 0.5)
            features['url_has_ip'] = 1
            features['url_suspicious_tld'] = 0
            features['url_subdomain_depth'] = 0
            features['url_path_length'] = np.random.randint(5, 40)
            features['url_has_https'] = np.random.choice([0, 1], p=[0.7, 0.3])
            features['url_brand_similarity'] = 0
            
        elif pattern == 'long_random':
            features['url_length'] = np.random.randint(100, 250)
            features['url_dot_count'] = np.random.randint(2, 5)
            features['url_hyphen_count'] = np.random.randint(2, 8)
            features['url_at_symbol'] = np.random.choice([0, 1], p=[0.7, 0.3])
            features['url_entropy'] = np.random.uniform(4.0, 6.0)
            features['url_digit_ratio'] = np.random.uniform(0.1, 0.4)
            features['url_has_ip'] = 0
            features['url_suspicious_tld'] = np.random.choice([0, 1], p=[0.4, 0.6])
            features['url_subdomain_depth'] = np.random.randint(0, 3)
            features['url_path_length'] = np.random.randint(40, 150)
            features['url_has_https'] = np.random.choice([0, 1], p=[0.5, 0.5])
            features['url_brand_similarity'] = np.random.uniform(0, 0.4)
            
        elif pattern == 'suspicious_tld':
            features['url_length'] = np.random.randint(30, 80)
            features['url_dot_count'] = np.random.randint(2, 5)
            features['url_hyphen_count'] = np.random.randint(0, 3)
            features['url_at_symbol'] = 0
            features['url_entropy'] = np.random.uniform(3.0, 5.0)
            features['url_digit_ratio'] = np.random.uniform(0.05, 0.25)
            features['url_has_ip'] = 0
            features['url_suspicious_tld'] = 1
            features['url_subdomain_depth'] = np.random.randint(0, 3)
            features['url_path_length'] = np.random.randint(5, 40)
            features['url_has_https'] = np.random.choice([0, 1], p=[0.6, 0.4])
            features['url_brand_similarity'] = np.random.uniform(0, 0.6)
            
        else:  # encoded
            features['url_length'] = np.random.randint(60, 200)
            features['url_dot_count'] = np.random.randint(2, 6)
            features['url_hyphen_count'] = np.random.randint(1, 4)
            features['url_at_symbol'] = np.random.choice([0, 1], p=[0.6, 0.4])
            features['url_entropy'] = np.random.uniform(4.5, 6.0)
            features['url_digit_ratio'] = np.random.uniform(0.15, 0.45)
            features['url_has_ip'] = np.random.choice([0, 1], p=[0.7, 0.3])
            features['url_suspicious_tld'] = np.random.choice([0, 1], p=[0.5, 0.5])
            features['url_subdomain_depth'] = np.random.randint(1, 4)
            features['url_path_length'] = np.random.randint(30, 100)
            features['url_has_https'] = np.random.choice([0, 1], p=[0.5, 0.5])
            features['url_brand_similarity'] = np.random.uniform(0.1, 0.7)
        
        # NLP features for phishing
        features['nlp_urgency_score'] = np.random.uniform(0.3, 1.0)
        features['nlp_threat_count'] = np.random.uniform(0.2, 1.0)
        features['nlp_credential_count'] = np.random.uniform(0.3, 1.0)
        features['nlp_action_count'] = np.random.uniform(0.3, 1.0)
        features['nlp_exclamation_ratio'] = np.random.uniform(0.05, 0.3)
        features['nlp_caps_ratio'] = np.random.uniform(0.1, 0.5)
        features['nlp_sender_impersonation'] = np.random.uniform(0.2, 1.0)
        features['nlp_ai_pattern_score'] = np.random.uniform(0.0, 0.8)
        
        # Structural features for phishing
        features['struct_href_mismatch'] = np.random.uniform(0.0, 0.8)
        features['struct_has_login_form'] = np.random.choice([0, 1], p=[0.3, 0.7])
        features['struct_hidden_ratio'] = np.random.uniform(0.0, 0.3)
        features['struct_homoglyph_count'] = np.random.uniform(0.0, 0.6)
        features['struct_obfuscation_score'] = np.random.uniform(0.0, 0.8)
        
        features['label'] = 1
        data.append(features)
    
    # === LEGITIMATE URLs (label=0) ===
    n_legit = n_samples - n_phishing
    for i in range(n_legit):
        features = {}
        features['url_length'] = np.random.randint(15, 60)
        features['url_dot_count'] = np.random.randint(1, 3)
        features['url_hyphen_count'] = np.random.randint(0, 2)
        features['url_at_symbol'] = 0
        features['url_entropy'] = np.random.uniform(2.5, 4.0)
        features['url_digit_ratio'] = np.random.uniform(0.0, 0.1)
        features['url_has_ip'] = 0
        features['url_suspicious_tld'] = 0
        features['url_subdomain_depth'] = np.random.choice([0, 1], p=[0.7, 0.3])
        features['url_path_length'] = np.random.randint(1, 30)
        features['url_has_https'] = np.random.choice([0, 1], p=[0.1, 0.9])
        features['url_brand_similarity'] = 0
        
        # NLP features for legit
        features['nlp_urgency_score'] = np.random.uniform(0.0, 0.2)
        features['nlp_threat_count'] = np.random.uniform(0.0, 0.1)
        features['nlp_credential_count'] = np.random.uniform(0.0, 0.15)
        features['nlp_action_count'] = np.random.uniform(0.0, 0.2)
        features['nlp_exclamation_ratio'] = np.random.uniform(0.0, 0.05)
        features['nlp_caps_ratio'] = np.random.uniform(0.0, 0.1)
        features['nlp_sender_impersonation'] = np.random.uniform(0.0, 0.1)
        features['nlp_ai_pattern_score'] = np.random.uniform(0.0, 0.3)
        
        # Structural features for legit
        features['struct_href_mismatch'] = 0
        features['struct_has_login_form'] = np.random.choice([0, 1], p=[0.85, 0.15])
        features['struct_hidden_ratio'] = np.random.uniform(0.0, 0.05)
        features['struct_homoglyph_count'] = 0
        features['struct_obfuscation_score'] = 0
        
        features['label'] = 0
        data.append(features)
    
    return pd.DataFrame(data)


def train_model():
    """Train the URL classifier model."""
    print("=" * 60)
    print("  VIGILANT — URL Classifier Training")
    print("=" * 60)
    
    # Load canonical training data
    print("\n[1/5] Loading canonical artifact (training_v3.parquet)...")
    parquet_path = os.path.join(os.path.dirname(__file__), 'training_v3.parquet')
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Canonical artifact not found at {parquet_path}. Run data_shim.py first.")
    
    df = pd.read_parquet(parquet_path)
    print(f"  Total samples: {len(df)}")
    print(f"  Phishing: {(df['label'] == 1).sum()}")
    print(f"  Legitimate: {(df['label'] == 0).sum()}")
    
    # Check for kill switch
    benign_authority_df = df[df['source'] == 'benign_authority']
    
    # Prepare features and labels
    print("\n[2/5] Preparing features (Enforcing exact feature order)...")
    X = df[ALL_FEATURE_NAMES].values
    y = df['label'].values
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Train XGBoost
    print("\n[3/5] Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss',
        use_label_encoder=False,
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    print("\n[4/5] Evaluating model...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n  Accuracy: {accuracy:.4f}")
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Phishing']))
    
    print(f"  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"    TN={cm[0][0]}  FP={cm[0][1]}")
    print(f"    FN={cm[1][0]}  TP={cm[1][1]}")
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"\n  5-Fold CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    # Feature importance
    print(f"\n  Top 10 Feature Importances:")
    importance = model.feature_importances_
    indices = np.argsort(importance)[::-1]
    for i in range(min(10, len(ALL_FEATURE_NAMES))):
        idx = indices[i]
        print(f"    {ALL_FEATURE_NAMES[idx]}: {importance[idx]:.4f}")
    
    print("\n[4.5/5] Executing Mandatory KILL-SWITCH Rule (Benign Authority FPs)...")
    if len(benign_authority_df) > 0:
        X_benigh_auth = benign_authority_df[ALL_FEATURE_NAMES].values
        y_pred_benign = model.predict(X_benigh_auth)
        fp_count = y_pred_benign.sum()  # Since true tag is 0
        fp_rate = fp_count / len(benign_authority_df)
        print(f"  Benign Authority FP Rate: {fp_rate:.4f} ({fp_count}/{len(benign_authority_df)})")
        
        if fp_rate > 0.01:
            raise RuntimeError(f"KILL-SWITCH ACTIVATED: Benign Authority False Positive Rate is {fp_rate:.2%}, which exceeds the 1.0% limit. ABORTING MODEL SAVE. DO NOT SHIP TO PROD.")
        else:
            print("  ✓ Guardrail passed. Saving models allowed.")
    else:
         print("  [WARN] No benign authority samples found in canonical artifact.")

    # Save model
    print("\n[5/5] Saving model v3.0...")
    os.makedirs(os.path.join(os.path.dirname(__file__), 'models'), exist_ok=True)
    model_path = os.path.join(os.path.dirname(__file__), 'models', 'url_classifier.joblib')
    joblib.dump(model, model_path)
    print(f"  Model saved to: {model_path}")
    
    # Save metadata
    meta_path = os.path.join(os.path.dirname(__file__), 'models', 'url_model_meta.json')
    meta = {
        "model_type": "XGBClassifier",
        "version": "v3.0",
        "schema_hash": get_feature_fingerprint(),
        "features": ALL_FEATURE_NAMES,
        "n_features": len(ALL_FEATURE_NAMES),
        "training_samples": len(df),
        "accuracy": round(accuracy, 4),
        "cv_accuracy_mean": round(cv_scores.mean(), 4),
        "cv_accuracy_std": round(cv_scores.std(), 4),
    }
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"  Metadata saved to: {meta_path}")
    
    print("\n" + "=" * 60)
    print("  ✓ Training complete!")
    print("=" * 60)
    
    return model


if __name__ == "__main__":
    train_model()
