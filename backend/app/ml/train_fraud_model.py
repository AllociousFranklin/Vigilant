"""SENTINEL ML - Transaction Fraud Classifier Training Script

Trains an XGBoost classifier on 30 transaction fraud features.
Evaluates precision, recall, F1, ROC-AUC on a held-out test set.
Enforces strict Kill-Switch Guardrail on high-value legitimate transactions.
"""
import os
import sys
import json
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report, accuracy_score, confusion_matrix,
    precision_score, recall_score, f1_score, roc_auc_score
)
from xgboost import XGBClassifier
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.engine.features import ALL_FEATURE_NAMES, get_feature_fingerprint


def train_model():
    print("=" * 60)
    print("  SENTINEL - Transaction Fraud Classifier Training (XGBoost)")
    print("=" * 60)

    # 1. Load canonical dataset
    print("\n[1/5] Loading canonical training artifact (training_v3.parquet)...")
    parquet_path = os.path.join(os.path.dirname(__file__), 'training_v3.parquet')
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Canonical artifact not found at {parquet_path}. Run data_shim.py first.")

    df = pd.read_parquet(parquet_path)
    print(f"  Total transactions: {len(df)}")
    print(f"  Fraud: {(df['label'] == 1).sum()}")
    print(f"  Legitimate: {(df['label'] == 0).sum()}")

    # Extract Kill-switch evaluation corpus (high-value legit txns)
    kill_switch_df = df[df['source'] == 'legit_high_value'].copy()
    print(f"  Kill-switch corpus size: {len(kill_switch_df)}")

    # 2. Prepare feature matrix (exclude kill-switch corpus to prevent data leakage)
    print("\n[2/5] Preparing feature matrix (30 features, strict schema ordering)...")
    df_trainable = df[df['source'] != 'legit_high_value'].copy()
    X = df_trainable[ALL_FEATURE_NAMES].values
    y = df_trainable['label'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"  Training set: {len(X_train)} | Held-out test set: {len(X_test)}")

    # 3. Train XGBoost
    print("\n[3/5] Training XGBoost ensemble classifier...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss',
    )
    model.fit(X_train, y_train)

    # 4. Evaluate on held-out test set
    print("\n[4/5] Evaluating performance on held-out test set...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    tpr = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0

    avg_legit_txn_inr = 4500.0
    fp_cost_inr = float(fp * avg_legit_txn_inr)

    print(f"\n  Accuracy : {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall   : {rec:.4f}")
    print(f"  F1 Score : {f1:.4f}")
    print(f"  ROC-AUC  : {auc:.4f}")
    print(f"  Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"  False Positive Rate: {fpr:.2%}")
    print(f"  False Positive Cost : INR {fp_cost_inr:,.2f}")

    # 5-fold cross validation on training set only (preventing test set leakage)
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
    print(f"  5-Fold CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # 4.5 Mandatory Kill-Switch Verification
    print("\n[4.5/5] Executing Mandatory KILL-SWITCH Guardrail (High-Value Legit Transactions)...")
    kill_switch_passed = False
    if len(kill_switch_df) > 0:
        X_ks = kill_switch_df[ALL_FEATURE_NAMES].values
        ks_preds = model.predict(X_ks)
        ks_fp = int(ks_preds.sum())
        ks_fp_rate = ks_fp / len(kill_switch_df)
        print(f"  Kill-switch evaluation: {ks_fp}/{len(kill_switch_df)} blocked ({ks_fp_rate:.2%})")

        if ks_fp_rate > 0.01:
            raise RuntimeError(
                f"KILL-SWITCH ACTIVATED: High-Value Legit False Positive Rate is {ks_fp_rate:.2%}, "
                f"which exceeds the 1.0% safety limit. ABORTING MODEL SAVE."
            )
        else:
            print("  [OK] Guardrail passed! False positive rate on high-value legit transactions is <= 1.0%.")
            kill_switch_passed = True
    else:
        print("  [WARN] No kill switch samples found.")

    # 5. Save model and comprehensive metadata
    print("\n[5/5] Saving model and metadata...")
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, 'fraud_classifier.joblib')
    joblib.dump(model, model_path)
    print(f"  Model saved to: {model_path}")

    meta = {
        "model_type": "XGBClassifier",
        "version": "v1.0",
        "schema_hash": get_feature_fingerprint(),
        "features": ALL_FEATURE_NAMES,
        "n_features": len(ALL_FEATURE_NAMES),
        "training_samples": len(df),
        "test_set_size": len(X_test),
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "auc_roc": round(float(auc), 4),
        "false_positive_rate": round(float(fpr), 4),
        "true_positive_rate": round(float(tpr), 4),
        "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
        "avg_legitimate_txn_amount": avg_legit_txn_inr,
        "false_positive_cost_inr": fp_cost_inr,
        "cv_f1_mean": round(float(cv_scores.mean()), 4),
        "cv_f1_std": round(float(cv_scores.std()), 4),
        "kill_switch_status": "PASSED" if kill_switch_passed else "FAILED",
        "last_trained": datetime.now(timezone.utc).isoformat(),
    }

    meta_path = os.path.join(model_dir, 'fraud_model_meta.json')
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"  Metadata saved to: {meta_path}")

    print("\n" + "=" * 60)
    print("  [OK] Fraud classifier training complete!")
    print("=" * 60)
    return model

if __name__ == "__main__":
    train_model()
