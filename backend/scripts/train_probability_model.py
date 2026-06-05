"""
ContestMind - Solve Probability Training Script
===============================================
Architecture: XGBoost + LightGBM + MLP(128→64→32) Stacking Ensemble
              with Logistic Regression meta-learner.

Features: 15 engineered features (7 original + 8 new).
Samples:  50 000 synthetic rows.
Output:
  app/ml_models/solve_prob_ensemble.joblib   — full stacking ensemble
  app/ml_models/solve_prob_scaler.joblib     — reference StandardScaler
  app/ml_models/solve_prob_metrics.json      — full evaluation report
"""

import os
import json
import random
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, roc_auc_score, f1_score, log_loss,
    precision_score, recall_score, brier_score_loss,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "app", "ml_models")
os.makedirs(MODELS_DIR, exist_ok=True)

ENSEMBLE_PATH = os.path.join(MODELS_DIR, "solve_prob_ensemble.joblib")
SCALER_PATH   = os.path.join(MODELS_DIR, "solve_prob_scaler.joblib")
METRICS_PATH  = os.path.join(MODELS_DIR, "solve_prob_metrics.json")

# ── Feature list (must match probability_service.py exactly) ─────────────────

FEATURES = [
    # Original 7
    "rating_difference",
    "user_max_rating_diff",
    "problem_index_encoded",
    "total_solved_count",
    "contest_maturity",
    "index_gap",
    "is_cold_start",
    # New 8
    "rating_ratio",
    "elo_baseline",
    "experience_tier",
    "difficulty_tier",
    "rating_volatility",
    "comfort_zone_distance",
    "solve_rate_proxy",
    "is_stretch_problem",
]


# ── Synthetic data generation ─────────────────────────────────────────────────

def generate_synthetic_data(num_samples: int = 50_000) -> pd.DataFrame:
    print(f"Generating {num_samples:,} synthetic rows…")
    rows = []
    for _ in range(num_samples):
        is_cold_start = random.random() < 0.10

        if is_cold_start:
            user_rating      = 800
            user_max_rating  = 800
            total_solved     = random.randint(0, 9)
            contest_maturity = 0
            avg_max_index    = 1.0
        else:
            user_rating      = random.randint(1000, 2400)
            user_max_rating  = user_rating + random.randint(0, 300)
            total_solved     = random.randint(50, 2000)
            contest_maturity = random.randint(5, 100)
            avg_max_index    = max(1.0, min(6.0, (user_rating - 800) / 300))

        problem_rating = random.randint(800, 3000)
        problem_index  = max(1, min(6, int((problem_rating - 800) / 300) + random.randint(-1, 1)))

        # ── Original 7 features ───────────────────────────────────────────
        rating_difference  = problem_rating - user_rating
        user_max_rating_diff = user_max_rating - user_rating
        index_gap          = problem_index - avg_max_index

        # ── New 8 features ────────────────────────────────────────────────
        rating_ratio           = problem_rating / max(user_rating, 1)
        elo_baseline           = 1.0 / (1.0 + 10.0 ** (rating_difference / 400.0))
        experience_tier        = min(4, total_solved // 250)          # 0-4
        difficulty_tier        = min(4, max(0, (problem_rating - 800) // 400))  # 0-4
        rating_volatility      = user_max_rating - user_rating        # 0 = consistent
        comfort_zone_center    = user_rating + 200
        comfort_zone_distance  = abs(problem_rating - comfort_zone_center)
        solve_rate_proxy       = total_solved / (contest_maturity + 1)
        is_stretch_problem     = 1 if problem_rating > user_rating + 200 else 0

        # ── Simulate solve probability ────────────────────────────────────
        adjusted_prob = elo_baseline
        if not is_cold_start:
            if total_solved > 1000:
                adjusted_prob += 0.05
            if index_gap >= 2.0:
                adjusted_prob -= 0.20
            elif index_gap <= -1.0:
                adjusted_prob += 0.10
            if is_stretch_problem:
                adjusted_prob -= 0.08
            if rating_volatility > 200:
                adjusted_prob += 0.03
        else:
            if problem_rating > 1000:
                adjusted_prob -= 0.50

        adjusted_prob = max(0.01, min(0.99, adjusted_prob))
        is_solved = 1 if random.random() < adjusted_prob else 0

        rows.append({
            "rating_difference":    rating_difference,
            "user_max_rating_diff": user_max_rating_diff,
            "problem_index_encoded": problem_index,
            "total_solved_count":   total_solved,
            "contest_maturity":     contest_maturity,
            "index_gap":            index_gap,
            "is_cold_start":        int(is_cold_start),
            "rating_ratio":         rating_ratio,
            "elo_baseline":         elo_baseline,
            "experience_tier":      experience_tier,
            "difficulty_tier":      difficulty_tier,
            "rating_volatility":    rating_volatility,
            "comfort_zone_distance": comfort_zone_distance,
            "solve_rate_proxy":     solve_rate_proxy,
            "is_stretch_problem":   is_stretch_problem,
            "is_solved":            is_solved,
        })

    return pd.DataFrame(rows)


# ── Training ──────────────────────────────────────────────────────────────────

def train_model():
    df = generate_synthetic_data(50_000)

    X = df[FEATURES]
    y = df["is_solved"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Train: {len(X_train):,}  |  Test: {len(X_test):,}")
    print(f"Class balance (train solved%): {y_train.mean():.1%}\n")

    # Reference scaler (tree models don't need it, MLP pipeline handles its own)
    ref_scaler = StandardScaler().fit(X_train)
    joblib.dump(ref_scaler, SCALER_PATH)
    print(f"Reference scaler saved ->{SCALER_PATH}")

    # ── Base learners ─────────────────────────────────────────────────────
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=42,
        verbosity=0,
    )
    lgb = LGBMClassifier(
        n_estimators=200,
        num_leaves=31,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1,
    )
    mlp_pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("mlp", MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation="relu",
            solver="adam",
            max_iter=200,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.10,
        )),
    ])

    # ── Stacking ensemble ─────────────────────────────────────────────────
    print("Building 3-model Stacking Ensemble:")
    print("  Layer 1: XGBoost(200) + LightGBM(200) + MLP(128->64->32)")
    print("  Layer 2: LogisticRegression meta-learner")
    print("  CV folds: 5   |   stack_method: predict_proba\n")

    stack = StackingClassifier(
        estimators=[
            ("xgb", xgb),
            ("lgb", lgb),
            ("mlp", mlp_pipe),
        ],
        final_estimator=LogisticRegression(C=1.0, random_state=42, max_iter=500),
        cv=5,
        stack_method="predict_proba",
        passthrough=False,
        n_jobs=-1,
    )

    print("Training… (this may take a few minutes due to 5-fold CV)")
    stack.fit(X_train, y_train)
    print("Training complete.\n")

    # ── Per-model baseline evaluation ─────────────────────────────────────
    print("-" * 55)
    print("Per-model AUC on held-out test set:")
    for name, est in stack.named_estimators_.items():
        try:
            proba = est.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, proba)
            print(f"  {name:6s}: AUC = {auc:.4f}")
        except Exception:
            pass

    # ── Ensemble evaluation ───────────────────────────────────────────────
    y_pred  = stack.predict(X_test)
    y_proba = stack.predict_proba(X_test)[:, 1]

    acc       = accuracy_score(y_test, y_pred)
    auc       = roc_auc_score(y_test, y_proba)
    f1        = f1_score(y_test, y_pred)
    ll        = log_loss(y_test, y_proba)
    prec      = precision_score(y_test, y_pred)
    rec       = recall_score(y_test, y_pred)
    brier     = brier_score_loss(y_test, y_proba)

    print("\n" + "-" * 55)
    print("Stacking Ensemble - Full Evaluation Report")
    print("-" * 55)
    print(f"  Accuracy:        {acc:.4f}")
    print(f"  AUC-ROC:         {auc:.4f}")
    print(f"  F1-Score:        {f1:.4f}")
    print(f"  Precision:       {prec:.4f}")
    print(f"  Recall:          {rec:.4f}")
    print(f"  Log-Loss:        {ll:.4f}")
    print(f"  Brier Score:     {brier:.4f}  (lower = better calibration)")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Not Solved", "Solved"]))

    # ── XGBoost feature importance ─────────────────────────────────────────
    xgb_model = stack.named_estimators_["xgb"]
    importances = dict(zip(FEATURES, xgb_model.feature_importances_.tolist()))
    ranked = sorted(importances.items(), key=lambda kv: kv[1], reverse=True)
    print("XGBoost Feature Importances (top 10):")
    for feat, imp in ranked[:10]:
        bar = "#" * int(imp * 200)
        print(f"  {feat:<28}  {imp:.4f}  {bar}")

    # ── Save artifacts ─────────────────────────────────────────────────────
    joblib.dump(stack, ENSEMBLE_PATH)
    print(f"\nEnsemble saved ->{ENSEMBLE_PATH}")

    metrics = {
        "model": "XGBoost + LightGBM + MLP Stacking Ensemble",
        "n_features": len(FEATURES),
        "features": FEATURES,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "accuracy": round(acc, 4),
        "auc_roc": round(auc, 4),
        "f1_score": round(f1, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "log_loss": round(ll, 4),
        "brier_score": round(brier, 4),
        "feature_importances": {k: round(v, 5) for k, v in ranked},
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved  ->{METRICS_PATH}")
    print("\nAll done.")


if __name__ == "__main__":
    train_model()
