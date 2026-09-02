"""
SENTINEL Test Suite - Precision, Recall & Honest Economic Metrics
Evaluates the trained model on a held-out test set (20% split) never seen during training.
Calculates honest metrics including False Positive Cost in INR.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    accuracy_score, confusion_matrix
)
import joblib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app.engine.features import ALL_FEATURE_NAMES
from app.core.config import settings


def run_precision_recall_evaluation():
    print("=" * 70)
    print("  SENTINEL - Held-Out Test Set Evaluation & Honest Metrics Report")
    print("=" * 70)

    parquet_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ml', 'training_v3.parquet')
    df = pd.read_parquet(parquet_path)

    df_eval = df[df['source'] != 'legit_high_value'].copy()
    X = df_eval[ALL_FEATURE_NAMES].values
    y = df_eval['label'].values

    # Exact same held-out split seed as training
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'ml', 'models', 'fraud_classifier.joblib')
    model = joblib.load(model_path)

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

    print(f"\nHeld-Out Test Evaluation Results (n={len(X_test)}):")
    print(f"  • Accuracy                : {acc:.4%}")
    print(f"  • Precision               : {prec:.4%}")
    print(f"  • Recall                  : {rec:.4%}")
    print(f"  • F1 Score                : {f1:.4%}")
    print(f"  • ROC-AUC Score           : {auc:.4f}")
    print(f"  • False Positive Rate     : {fpr:.2%}")
    print(f"  • True Positive Rate      : {tpr:.2%}")
    print(f"  • Confusion Matrix        : TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"  • False Positive Cost(INR): INR {fp_cost_inr:,.2f}")

    # Explicit threshold checks per Razorpay requirements
    assert prec >= 0.85, f"Precision failed threshold: {prec:.4f} < 0.85"
    assert rec >= 0.80, f"Recall failed threshold: {rec:.4f} < 0.80"
    assert fpr <= 0.02, f"False positive rate too high: {fpr:.2%} > 2.0%"

    # Output directory for test reports
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'test_results')
    os.makedirs(reports_dir, exist_ok=True)
    report_file = os.path.join(reports_dir, 'precision_recall_report.json')

    report_data = {
        "test_suite": "Held-Out Test Set Evaluation",
        "sample_size": len(X_test),
        "metrics": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(auc), 4),
            "false_positive_rate": round(float(fpr), 4),
            "true_positive_rate": round(float(tpr), 4),
            "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
            "false_positive_cost_inr": fp_cost_inr,
        },
        "status": "PASSED"
    }

    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"\n[OK] Saved honest evaluation report to: {report_file}")
    print("=" * 70)


if __name__ == "__main__":
    run_precision_recall_evaluation()
