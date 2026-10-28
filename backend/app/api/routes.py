"""
backend/app/api/routes.py - Core API Endpoints
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

import time
import os
import json
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from backend.app.schemas.triage import TriageRequest, TriageResponse, RulesResponse, RuleDefinition, CleanedIntake
from backend.app.ml.data_cleaner import clean_patient_record
from backend.app.safety.rules import evaluate_rules, get_rules_table
from backend.app.ml.pipeline import SmartTriagePipeline
from backend.queue_simulator import run_comparative_simulation

router = APIRouter(prefix="/api", tags=["triage"])

LEVEL_NAMES = {
    0: "CANNOT ASSESS - SEND TO NURSE NOW",
    1: "Level 1: Resuscitation / Immediate",
    2: "Level 2: Emergent / Very Urgent",
    3: "Level 3: Urgent",
    4: "Level 4: Less Urgent",
    5: "Level 5: Non-Urgent",
}

LEVEL_COLORS = {
    0: "#8b5cf6", # Purple
    1: "#ef4444", # Red
    2: "#f97316", # Orange
    3: "#eab308", # Yellow
    4: "#22c55e", # Green
    5: "#3b82f6", # Blue
}

# Cached pipeline & metrics
_pipeline = None
_metrics = None


def get_active_pipeline():
    global _pipeline
    if _pipeline is None:
        model_path = os.path.join("models", "model_bundle.joblib")
        if os.path.exists(model_path):
            _pipeline = SmartTriagePipeline.load(model_path)
        else:
            from backend.train import train_and_evaluate
            _pipeline, _ = train_and_evaluate()
    return _pipeline


def get_cached_metrics():
    global _metrics
    if _metrics is None:
        metrics_path = os.path.join("models", "metrics.json")
        if os.path.exists(metrics_path):
            with open(metrics_path, "r", encoding="utf-8") as f:
                _metrics = json.load(f)
        else:
            from backend.train import train_and_evaluate
            _, _metrics = train_and_evaluate()
    return _metrics


@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "SmartTriage AI", "version": "1.0.0"}


@router.post("/triage", response_model=TriageResponse)
def triage_patient(request: TriageRequest):
    """
    Main Triage Decision Support Endpoint (< 200 ms).
    Enforces deterministic safety rules before calibrated ML inference.
    """
    start_t = time.perf_counter()
    raw_dict = request.model_dump()
    pipeline = get_active_pipeline()

    # 1. Clean intake
    cleaned = clean_patient_record(raw_dict)

    # 2. Rule Engine check
    rule_res = evaluate_rules(cleaned)

    # 3. Model inference
    ml_res = pipeline.predict_single(raw_dict, use_cost_minimizer=True)

    # 4. Priority arbitration
    final_level = ml_res["model_level"]
    rule_override = False
    active_rule = None
    recommended_dept = ml_res["recommended_department"]

    if rule_res["rule_triggered"]:
        r_level = rule_res["rule_level"]
        active_rule = rule_res["rule_name"]
        if r_level < final_level:
            final_level = r_level
            rule_override = True
        if rule_res.get("rule_department"):
            recommended_dept = rule_res["rule_department"]

    if cleaned["is_pediatric"] and final_level not in [1, 2]:
        recommended_dept = "Pediatrics"

    # 5. Abstention
    is_abstain = False
    abstain_reason = None
    if ml_res["should_abstain"] and not rule_override:
        is_abstain = True
        abstain_reason = ml_res["abstain_reason"]
        final_level = 0

    # 6. Clinical reasoning
    clinical_why = []
    if is_abstain:
        clinical_why.append(f"ABSTENTION TRIGGERED: {abstain_reason}. Handing over to triage nurse.")
    else:
        if rule_override:
            clinical_why.append(f"SAFETY OVERRIDE: Rule '{active_rule}' overrode ML prediction to Level {final_level}.")
        else:
            clinical_why.append(f"COST-OPTIMAL DECISION: Level {final_level} selected to minimize asymmetric mortality risk.")

    for reason in rule_res["clinical_reasons"]:
        clinical_why.append(reason)
    for alert in rule_res["nurse_alerts"]:
        clinical_why.append(f"ADVISORY: {alert}")
    for warn in cleaned["warnings"]:
        clinical_why.append(f"DATA SANITIZATION: {warn}")
    clinical_why.append(
        f"MODEL CONFIDENCE: {ml_res['confidence']*100:.1f}% on primary class (Calibrated dual-ngram TF-IDF)."
    )

    is_emergency = (final_level in [1, 2])
    latency_ms = round((time.perf_counter() - start_t) * 1000, 2)

    cleaned_schema = CleanedIntake(
        age=cleaned["age"],
        sex=cleaned["sex"],
        is_pediatric=cleaned["is_pediatric"],
        chief_complaint=cleaned["chief_complaint"],
        bp_systolic=cleaned["bp_systolic"],
        bp_diastolic=cleaned["bp_diastolic"],
        heart_rate=cleaned["heart_rate"],
        respiratory_rate=cleaned["respiratory_rate"],
        temperature=cleaned["temperature"],
        spo2=cleaned["spo2"],
    )

    return TriageResponse(
        patient_id=cleaned["patient_id"],
        triage_level=final_level,
        triage_level_name=LEVEL_NAMES.get(final_level, f"Level {final_level}"),
        color_code=LEVEL_COLORS.get(final_level, "#64748b"),
        is_emergency=is_emergency,
        recommended_department=recommended_dept,
        rule_override=rule_override,
        rule_applied=active_rule,
        is_abstain=is_abstain,
        abstain_reason=abstain_reason,
        red_flags=rule_res["red_flag_chips"],
        clinical_why=clinical_why,
        nurse_alerts=rule_res["nurse_alerts"],
        data_warnings=cleaned["warnings"],
        probabilities=ml_res["probabilities"],
        expected_costs=ml_res["expected_costs"],
        latency_ms=latency_ms,
        disclaimer="DECISION SUPPORT ONLY — CLINICAL NURSE / ATTENDING PHYSICIAN DECIDES",
        cleaned_intake=cleaned_schema,
    )


@router.get("/rules", response_model=RulesResponse)
def get_rules():
    rules_data = get_rules_table()
    rule_objs = [RuleDefinition(**r) for r in rules_data]
    return RulesResponse(
        total_rules=len(rule_objs),
        rules=rule_objs,
        disclaimer="Rules run prior to ML and strictly override the model for patient safety."
    )


@router.get("/metrics")
def get_metrics():
    return get_cached_metrics()


@router.post("/simulate")
def run_simulation():
    arrival_path = os.path.join("data", "arrival_log.csv")
    return run_comparative_simulation(arrival_path)
