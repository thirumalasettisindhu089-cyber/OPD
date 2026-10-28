"""
backend/train.py - Training, Calibration, and 4-Stage Ablation Evaluation
SmartTriage AI - Talent AP Mega Hackathon 2026

Runs:
1. Data ingestion with column remapping & cleaning
2. Stratified Train / Validation split
3. Baseline (Logistic Regression) vs Calibrated LinearSVC training
4. 4-Stage Ablation Benchmark:
   - Stage 1: Plain Argmax (Naive ML)
   - Stage 2: Asymmetric Cost-Aware Decision Rule
   - Stage 3: Cost-Aware + Deterministic Rule Engine Override
   - Stage 4: Full System (Cost-Aware + Rule Override + Uncertainty Abstention)
5. Metric serialization for FastAPI GET /api/metrics
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from backend.data_cleaner import remap_dataframe_columns, clean_patient_record
from backend.rule_engine import evaluate_rules
from backend.model import SmartTriagePipeline
from backend.queue_simulator import run_comparative_simulation
from evaluate import calculate_metrics, print_evaluation_report


def run_ablation_evaluation(
    pipeline: SmartTriagePipeline,
    val_df: pd.DataFrame
) -> dict:
    """
    Evaluates the 4 required ablation stages on the validation split:
    1. Plain Argmax
    2. Cost-Aware
    3. Cost-Aware + Rules
    4. Cost-Aware + Rules + Abstention (Full SmartTriage AI)
    """
    X_val = pipeline._prepare_feature_matrices(val_df, fit=False)
    y_true_level = val_df["triage_level"].to_numpy(dtype=int)
    y_true_dept = val_df["recommended_department"].to_numpy(dtype=str)
    is_emergency = val_df["true_emergency"].to_numpy(dtype=int) == 1

    probs = pipeline.predict_probabilities(X_val)
    dept_preds = pipeline.dept_model.predict(X_val)

    n_samples = len(val_df)

    # 1. Plain Argmax predictions
    y_pred_argmax = np.argmax(probs, axis=1) + 1

    # 2. Cost-Aware predictions
    y_pred_cost_aware = np.zeros(n_samples, dtype=int)
    for i in range(n_samples):
        lvl, _ = pipeline.predict_cost_minimizing_level(probs[i])
        y_pred_cost_aware[i] = lvl

    # 3. Cost-Aware + Rules Engine predictions
    y_pred_rules = np.copy(y_pred_cost_aware)
    rules_applied = np.zeros(n_samples, dtype=bool)
    val_records = val_df.to_dict(orient="records")

    for i in range(n_samples):
        rule_res = evaluate_rules(val_records[i])
        if rule_res["rule_triggered"]:
            r_lvl = rule_res["rule_level"]
            # Rule overrides if pointing to higher urgency (lower level number)
            if r_lvl < y_pred_rules[i]:
                y_pred_rules[i] = r_lvl
                rules_applied[i] = True

    # 4. Cost-Aware + Rules + Abstention (Full Pipeline)
    y_pred_full = np.copy(y_pred_rules)
    is_abstain = np.zeros(n_samples, dtype=bool)

    for i in range(n_samples):
        should_ab, _ = pipeline.check_abstention(probs[i], val_records[i])
        if should_ab:
            # If a critical rule did NOT already catch an emergency, abstain
            if not rules_applied[i]:
                is_abstain[i] = True
                y_pred_full[i] = 0  # 0 denotes abstain

    # Compute metrics for all 4 ablations
    m_argmax = calculate_metrics(y_true_level, y_pred_argmax, y_true_dept, dept_preds, is_emergency)
    m_cost = calculate_metrics(y_true_level, y_pred_cost_aware, y_true_dept, dept_preds, is_emergency)
    m_rules = calculate_metrics(y_true_level, y_pred_rules, y_true_dept, dept_preds, is_emergency)
    m_full = calculate_metrics(y_true_level, y_pred_full, y_true_dept, dept_preds, is_emergency, is_abstain)

    return {
        "plain_argmax": m_argmax,
        "cost_aware": m_cost,
        "cost_aware_plus_rules": m_rules,
        "full_pipeline": m_full,
    }


def train_and_evaluate(
    data_path: str = "data/dataset.csv",
    model_save_path: str = "models/model_bundle.joblib",
    metrics_save_path: str = "models/metrics.json"
):
    print("=" * 78)
    print(" SMARTTRIAGE AI - TRAINING & ABLATION BENCHMARK ")
    print("=" * 78)

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}. Run generate_synthetic_data.py first!")

    print(f"[*] Ingesting and remapping dataset from {data_path}...")
    df_raw = pd.read_csv(data_path)
    df = remap_dataframe_columns(df_raw)

    print(f"[+] Loaded {len(df):,} patient records.")

    # Clean records
    print("[*] Preprocessing intake records with clinical sanitization & alias mapping...")
    cleaned_rows = [clean_patient_record(row) for row in df.to_dict(orient="records")]
    df_clean = pd.DataFrame(cleaned_rows)

    # Train / Validation split (80/20 stratified on triage level)
    print("[*] Creating 80/20 stratified Train/Validation split...")
    df_train, df_val = train_test_split(
        df_clean,
        test_size=0.20,
        random_state=42,
        stratify=df_clean["triage_level"]
    )
    print(f"[+] Train split: {len(df_train):,} samples | Validation split: {len(df_val):,} samples")

    # Fit pipeline
    pipeline = SmartTriagePipeline()
    print("[*] Fitting dual-ngram TF-IDF vectorizers, imputer, and calibrated classifiers...")
    pipeline.fit(df_train)
    print("[+] Model training and probability calibration complete.")

    # Run ablations
    print("\n[*] Evaluating 4 pipeline stages against validation set...")
    ablations = run_ablation_evaluation(pipeline, df_val)

    # Print reports
    print("\n" + "#" * 78)
    print_evaluation_report(ablations["plain_argmax"], "STAGE 1: NAIVE PLAIN ARGMAX (STANDARD ML)")
    print("\n" + "#" * 78)
    print_evaluation_report(ablations["cost_aware"], "STAGE 2: ASYMMETRIC COST-AWARE DECISION RULE")
    print("\n" + "#" * 78)
    print_evaluation_report(ablations["cost_aware_plus_rules"], "STAGE 3: COST-AWARE + DETERMINISTIC RULE ENGINE")
    print("\n" + "#" * 78)
    print_evaluation_report(ablations["full_pipeline"], "STAGE 4: FULL SMARTTRIAGE AI (+ ABSTENTION MECHANISM)")

    # Run queue simulation
    print("\n[*] Running OPD queue wait-time simulation (FCFS vs SmartTriage AI)...")
    sim_results = run_comparative_simulation("data/arrival_log.csv")

    # Save model and metrics
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    pipeline.save(model_save_path)

    bundle_metrics = {
        "dataset_name": "Synthetic Government District Hospital OPD Cohort (Talent AP H1)",
        "synthetic_data_disclaimer": "NOTE: Synthetic data generated strictly according to Talent AP H1 clinical specifications. Real clinical deployment requires local IRB validation.",
        "val_samples": len(df_val),
        "ablations": ablations,
        "queue_simulation": sim_results,
    }

    with open(metrics_save_path, "w", encoding="utf-8") as f:
        json.dump(bundle_metrics, f, indent=2)
    print(f"[+] Serialized metrics to {metrics_save_path}")

    return pipeline, bundle_metrics


if __name__ == "__main__":
    train_and_evaluate()
