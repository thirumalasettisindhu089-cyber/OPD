"""
backend/main.py - SmartTriage AI FastAPI Backend
SmartTriage AI - Talent AP Mega Hackathon 2026

Endpoints:
- POST /api/triage: Near-instant (<200ms) triage decision support
- GET /api/rules: Complete clinical rule table
- GET /api/metrics: Validation benchmark, 4-stage ablations, emergency recall
- POST /api/simulate: OPD queue wait-time simulation (FCFS vs SmartTriage AI)
- GET /: OPD Triage Cockpit Web Interface
"""

import os
import time
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import VITALS_THRESHOLDS
from backend.data_cleaner import clean_patient_record
from backend.rule_engine import evaluate_rules, get_rules_table
from backend.model import SmartTriagePipeline
from backend.queue_simulator import run_comparative_simulation

# Initialize FastAPI
app = FastAPI(
    title="SmartTriage AI - Clinical Decision Support",
    description="OPD Triage Assistant for High-Volume Government Hospitals (Talent AP H1)",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model and metrics cache
PIPELINE: Optional[SmartTriagePipeline] = None
METRICS_CACHE: Optional[Dict[str, Any]] = None

MODEL_PATH = os.path.join("models", "model_bundle.joblib")
METRICS_PATH = os.path.join("models", "metrics.json")

LEVEL_NAMES = {
    0: "CANNOT ASSESS - SEND TO NURSE NOW",
    1: "Level 1: Resuscitation / Immediate",
    2: "Level 2: Emergent / Very Urgent",
    3: "Level 3: Urgent",
    4: "Level 4: Less Urgent",
    5: "Level 5: Non-Urgent",
}

LEVEL_COLORS = {
    0: "#8b5cf6", # Purple / Attention
    1: "#ef4444", # Red
    2: "#f97316", # Orange
    3: "#eab308", # Yellow
    4: "#22c55e", # Green
    5: "#3b82f6", # Blue
}


def get_pipeline() -> SmartTriagePipeline:
    global PIPELINE
    if PIPELINE is None:
        if os.path.exists(MODEL_PATH):
            PIPELINE = SmartTriagePipeline.load(MODEL_PATH)
        else:
            # Fallback: create fresh pipeline and fit on default dataset
            from backend.train import train_and_evaluate
            PIPELINE, _ = train_and_evaluate()
    return PIPELINE


def get_metrics() -> Dict[str, Any]:
    global METRICS_CACHE
    if METRICS_CACHE is None:
        if os.path.exists(METRICS_PATH):
            with open(METRICS_PATH, "r", encoding="utf-8") as f:
                METRICS_CACHE = json.load(f)
        else:
            from backend.train import train_and_evaluate
            _, METRICS_CACHE = train_and_evaluate()
    return METRICS_CACHE


class TriageRequest(BaseModel):
    patient_id: Optional[str] = Field(default="WALK_IN_01")
    age: Optional[int] = Field(default=35, ge=0, le=120)
    sex: Optional[str] = Field(default="M")
    chief_complaint: str = Field(default="", description="Free text complaint in EN, TE, or HI")
    bp_systolic: Optional[float] = Field(default=None)
    bp_diastolic: Optional[float] = Field(default=None)
    heart_rate: Optional[float] = Field(default=None)
    respiratory_rate: Optional[float] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    spo2: Optional[float] = Field(default=None)
    known_conditions: Optional[str] = Field(default="None")
    current_medications: Optional[str] = Field(default="None")


@app.on_event("startup")
def startup_event():
    # Warm up model and metrics
    try:
        get_pipeline()
        get_metrics()
        print("[+] SmartTriage AI backend ready and warmed up.")
    except Exception as e:
        print(f"[!] Startup warning: {e}")


@app.post("/api/triage")
def triage_patient(request: TriageRequest):
    """
    Main Triage Decision Support Endpoint (< 200 ms).
    Enforces deterministic safety rules prior to calibrated ML model inference.
    """
    start_t = time.perf_counter()

    raw_dict = request.model_dump()
    pipeline = get_pipeline()

    # 1. Data Cleaning & Sanitization
    cleaned = clean_patient_record(raw_dict)

    # 2. Deterministic Rule Engine Evaluation (Safety First)
    rule_res = evaluate_rules(cleaned)

    # 3. Probabilistic ML Model Inference
    ml_res = pipeline.predict_single(raw_dict, use_cost_minimizer=True)

    # 4. Asymmetric Safety Arbitration
    final_level = ml_res["model_level"]
    rule_override = False
    active_rule = None
    recommended_dept = ml_res["recommended_department"]

    # Rule Engine Priority Override:
    # If a rule triggered an emergency level (1 or 2):
    if rule_res["rule_triggered"]:
        r_level = rule_res["rule_level"]
        active_rule = rule_res["rule_name"]
        if r_level < final_level:
            final_level = r_level
            rule_override = True
        # If the rule has a specific clinical department (e.g. Cardiology, Pulmonology), adopt it
        if rule_res.get("rule_department"):
            recommended_dept = rule_res["rule_department"]

    # If pediatric patient and non-emergency, route to Pediatrics department
    if cleaned["is_pediatric"] and final_level not in [1, 2]:
        recommended_dept = "Pediatrics"

    # 5. Abstention Evaluation
    # If ML requests abstention AND no deterministic critical rule triggered
    is_abstain = False
    abstain_reason = None
    if ml_res["should_abstain"] and not rule_override:
        is_abstain = True
        abstain_reason = ml_res["abstain_reason"]
        final_level = 0  # Abstain state

    # 6. Synthesize Clinical Reasoning ("Why" list)
    clinical_why = []
    if is_abstain:
        clinical_why.append(f"ABSTENTION TRIGGERED: {abstain_reason}. Handing over to triage nurse.")
    else:
        if rule_override:
            clinical_why.append(f"SAFETY OVERRIDE: Rule '{active_rule}' overrode ML prediction to Level {final_level}.")
        else:
            clinical_why.append(
                f"COST-OPTIMAL DECISION: Level {final_level} selected to minimize asymmetric mortality risk."
            )

    # Add rule reasons
    for reason in rule_res["clinical_reasons"]:
        clinical_why.append(reason)

    # Add nurse alerts
    for alert in rule_res["nurse_alerts"]:
        clinical_why.append(f"ADVISORY: {alert}")

    # Add data cleaner warnings
    for warn in cleaned["warnings"]:
        clinical_why.append(f"DATA SANITIZATION: {warn}")

    # Add ML confidence context
    clinical_why.append(
        f"MODEL CONFIDENCE: {ml_res['confidence']*100:.1f}% on primary class (Evaluated via calibrated dual-ngram TF-IDF)."
    )

    is_emergency = (final_level in [1, 2])
    latency_ms = round((time.perf_counter() - start_t) * 1000, 2)

    return {
        "patient_id": cleaned["patient_id"],
        "triage_level": final_level,
        "triage_level_name": LEVEL_NAMES.get(final_level, f"Level {final_level}"),
        "color_code": LEVEL_COLORS.get(final_level, "#64748b"),
        "is_emergency": is_emergency,
        "recommended_department": recommended_dept,
        "rule_override": rule_override,
        "rule_applied": active_rule,
        "is_abstain": is_abstain,
        "abstain_reason": abstain_reason,
        "red_flags": rule_res["red_flag_chips"],
        "clinical_why": clinical_why,
        "nurse_alerts": rule_res["nurse_alerts"],
        "data_warnings": cleaned["warnings"],
        "probabilities": ml_res["probabilities"],
        "expected_costs": ml_res["expected_costs"],
        "latency_ms": latency_ms,
        "disclaimer": "DECISION SUPPORT ONLY — CLINICAL NURSE / PHYSICIAN DECIDES",
        "cleaned_intake": {
            "age": cleaned["age"],
            "sex": cleaned["sex"],
            "is_pediatric": cleaned["is_pediatric"],
            "chief_complaint": cleaned["chief_complaint"],
            "bp_systolic": cleaned["bp_systolic"],
            "bp_diastolic": cleaned["bp_diastolic"],
            "heart_rate": cleaned["heart_rate"],
            "respiratory_rate": cleaned["respiratory_rate"],
            "temperature": cleaned["temperature"],
            "spo2": cleaned["spo2"],
        }
    }


@app.get("/api/rules")
def get_rules():
    """Returns the complete, transparent deterministic clinical rule table."""
    return {
        "total_rules": len(get_rules_table()),
        "rules": get_rules_table(),
        "disclaimer": "Rules run prior to ML and strictly override the model for patient safety."
    }


@app.get("/api/metrics")
def get_benchmark_metrics():
    """Returns official evaluation benchmark with 4-stage ablations and emergency recall."""
    metrics = get_metrics()
    return metrics


@app.post("/api/simulate")
def run_simulation():
    """Runs OPD queue simulation comparing FCFS vs SmartTriage AI Priority Queue."""
    sim_data = run_comparative_simulation("data/arrival_log.csv")
    return sim_data


# Mount frontend static directory if exists
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/styles.css")
    def serve_styles():
        return FileResponse(os.path.join(frontend_dir, "styles.css"), media_type="text/css")

    @app.get("/app.js")
    def serve_script():
        return FileResponse(os.path.join(frontend_dir, "app.js"), media_type="application/javascript")

