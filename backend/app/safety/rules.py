"""
backend/app/safety/rules.py - Pure Python Clinical Escalation & Rule Engine
SmartTriage AI - Talent AP Mega Hackathon 2026

Deterministic safety layer running prior to ML models.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from backend.config import VITALS_THRESHOLDS, RED_FLAG_PATTERNS, NEGATION_TERMS


def is_negated(text: str, match_start: int, match_end: int, window_chars: int = 35) -> bool:
    """Checks whether symptom occurrence in text is preceded or followed by negation words."""
    start_window = max(0, match_start - window_chars)
    end_window = min(len(text), match_end + window_chars)

    pre_text = text[start_window:match_start].lower()
    post_text = text[match_end:end_window].lower()

    all_negators = (
        NEGATION_TERMS["en"] +
        NEGATION_TERMS["te"] +
        NEGATION_TERMS["hi"]
    )

    for neg in all_negators:
        pattern = r"\b" + re.escape(neg) + r"\b"
        if re.search(pattern, pre_text) or re.search(pattern, post_text):
            return True
    return False


def detect_red_flags(clean_complaint: str) -> List[Dict[str, Any]]:
    """Detects un-negated multilingual red-flag symptoms in cleaned text."""
    detected = []
    if not clean_complaint:
        return detected

    for category, cfg in RED_FLAG_PATTERNS.items():
        for keyword in cfg["keywords"]:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            for match in re.finditer(pattern, clean_complaint):
                start, end = match.span()
                if not is_negated(clean_complaint, start, end):
                    detected.append({
                        "category": category,
                        "matched_term": keyword,
                        "default_level": cfg["default_level"],
                        "department": cfg["department"],
                        "description": cfg["description"]
                    })
                    break
    return detected


def evaluate_rules(record: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates vitals and red flags deterministically."""
    age = record.get("age", 35)
    is_pediatric = record.get("is_pediatric", age < 12)
    flags = record.get("flags", {})

    sbp = record.get("bp_systolic")
    hr = record.get("heart_rate")
    rr = record.get("respiratory_rate")
    temp = record.get("temperature")
    spo2 = record.get("spo2")
    complaint = record.get("chief_complaint", "")

    rule_level: Optional[int] = None
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    rule_department: Optional[str] = None
    clinical_reasons: List[str] = []
    red_flag_chips: List[str] = []
    nurse_alerts: List[str] = []

    vt = VITALS_THRESHOLDS

    # 1. Pediatric Protocol Bypass
    if is_pediatric:
        nurse_alerts.append(
            f"PEDIATRIC PATIENT (Age {age} < 12): Adult vital sign cutoffs bypassed. Apply pediatric PALS / Broselow protocol."
        )

    # 2. Vital Signs Rules (Adult only)
    if not is_pediatric:
        # Level 1 Resuscitation
        if sbp is not None and not flags.get("bp_systolic_missing") and sbp < vt["bp_systolic"]["critical_low_l1"]:
            rule_level = 1
            rule_id = "VITAL_L1_PROFOUND_SHOCK"
            rule_name = "Profound Hemodynamic Shock (SBP < 70 mmHg)"
            rule_department = "Emergency / Cardiology"
            clinical_reasons.append(f"CRITICAL VITAL: Systolic BP {sbp:.0f} mmHg indicates profound shock/hypotension.")

        if spo2 is not None and not flags.get("spo2_missing") and spo2 < vt["spo2"]["critical_low_l1"]:
            rule_level = 1
            rule_id = "VITAL_L1_SEVERE_HYPOXIA"
            rule_name = "Severe Life-Threatening Hypoxia (SpO2 < 85%)"
            rule_department = "Pulmonology"
            clinical_reasons.append(f"CRITICAL VITAL: SpO2 {spo2:.0f}% indicates severe refractory hypoxia.")

        if hr is not None and not flags.get("heart_rate_missing") and (hr < vt["heart_rate"]["critical_low_l1"] or hr > vt["heart_rate"]["critical_high_l1"]):
            rule_level = 1
            rule_id = "VITAL_L1_EXTREME_HEART_RATE"
            rule_name = f"Extreme Heart Rate Disruption ({hr:.0f} bpm)"
            rule_department = "Emergency / Cardiology"
            clinical_reasons.append(f"CRITICAL VITAL: Heart rate {hr:.0f} bpm is at extreme arrest threshold (<40 or >160).")

        if rr is not None and not flags.get("respiratory_rate_missing") and (rr < vt["respiratory_rate"]["critical_low_l1"] or rr > vt["respiratory_rate"]["critical_high_l1"]):
            rule_level = 1
            rule_id = "VITAL_L1_RESPIRATORY_FAILURE"
            rule_name = f"Impending Respiratory Arrest (RR {rr:.0f} bpm)"
            rule_department = "Pulmonology"
            clinical_reasons.append(f"CRITICAL VITAL: Respiratory rate {rr:.0f} bpm indicates respiratory exhaustion (<8 or >38).")

        # Level 2 Emergent
        if rule_level is None:
            if sbp is not None and not flags.get("bp_systolic_missing"):
                if sbp < vt["bp_systolic"]["emergent_low_l2"]:
                    rule_level = 2
                    rule_id = "VITAL_L2_HYPOTENSION"
                    rule_name = "Emergent Hypotension (SBP 70-89 mmHg)"
                    rule_department = "Emergency / Cardiology"
                    clinical_reasons.append(f"EMERGENT VITAL: Systolic BP {sbp:.0f} mmHg indicates pre-shock hypoperfusion.")
                elif sbp >= vt["bp_systolic"]["emergent_high_l2"]:
                    rule_level = 2
                    rule_id = "VITAL_L2_HYPERTENSIVE_CRISIS"
                    rule_name = "Hypertensive Crisis (SBP >= 200 mmHg)"
                    rule_department = "Emergency / Cardiology"
                    clinical_reasons.append(f"EMERGENT VITAL: Systolic BP {sbp:.0f} mmHg indicates acute hypertensive crisis.")

            if spo2 is not None and not flags.get("spo2_missing") and spo2 < vt["spo2"]["emergent_low_l2"]:
                rule_level = 2
                rule_id = "VITAL_L2_MODERATE_HYPOXIA"
                rule_name = "Acute Hypoxia (SpO2 85-89%)"
                rule_department = "Pulmonology"
                clinical_reasons.append(f"EMERGENT VITAL: SpO2 {spo2:.0f}% requires high-flow supplemental oxygen.")

            if hr is not None and not flags.get("heart_rate_missing") and hr >= vt["heart_rate"]["emergent_high_l2"]:
                rule_level = 2
                rule_id = "VITAL_L2_TACHYCARDIA"
                rule_name = f"Severe Tachycardia ({hr:.0f} bpm)"
                rule_department = "Emergency / Cardiology"
                clinical_reasons.append(f"EMERGENT VITAL: Severe tachycardia {hr:.0f} bpm.")

            if rr is not None and not flags.get("respiratory_rate_missing") and rr >= vt["respiratory_rate"]["emergent_high_l2"]:
                rule_level = 2
                rule_id = "VITAL_L2_TACHYPNEA"
                rule_name = f"Severe Tachypnea (RR {rr:.0f} bpm)"
                rule_department = "Pulmonology"
                clinical_reasons.append(f"EMERGENT VITAL: Tachypnea {rr:.0f} breaths/min indicates respiratory distress.")

            if temp is not None and not flags.get("temperature_missing") and temp >= vt["temperature_c"]["emergent_hyperpyrexia_l2"]:
                if hr is not None and hr > 100:
                    rule_level = 2
                    rule_id = "VITAL_L2_HYPERPYREXIA_SEPSIS"
                    rule_name = f"Hyperpyrexia with Tachycardia ({temp:.1f}°C, {hr:.0f} bpm)"
                    rule_department = "General Medicine"
                    clinical_reasons.append(f"EMERGENT VITAL: High fever {temp:.1f}°C with tachycardia indicates possible severe sepsis.")

    # 3. Multilingual Red-Flag Symptoms (All ages)
    red_flags = detect_red_flags(complaint)
    for rf in red_flags:
        rf_term = rf["matched_term"]
        rf_desc = rf["description"]
        rf_level = rf["default_level"]
        red_flag_chips.append(f"{rf['category'].upper()}: {rf_term}")

        if rf["category"] == "anaphylaxis":
            rule_level = 1
            rule_id = "RED_FLAG_L1_ANAPHYLAXIS"
            rule_name = "Airway-Threatening Anaphylaxis"
            rule_department = "Emergency / Cardiology"
            clinical_reasons.append(f"RED FLAG: {rf_desc} detected ('{rf_term}'). Immediate resuscitation required.")
        elif rule_level is None or rf_level < rule_level:
            rule_level = rf_level
            rule_id = f"RED_FLAG_L{rf_level}_{rf['category'].upper()}"
            rule_name = f"Red Flag: {rf_desc}"
            rule_department = rf["department"]
            clinical_reasons.append(f"RED FLAG: {rf_desc} identified ('{rf_term}').")

    return {
        "rule_triggered": (rule_level is not None),
        "rule_level": rule_level,
        "rule_id": rule_id,
        "rule_name": rule_name,
        "rule_department": rule_department,
        "clinical_reasons": clinical_reasons,
        "red_flag_chips": red_flag_chips,
        "nurse_alerts": nurse_alerts,
        "pediatric_bypassed": is_pediatric,
    }


def get_rules_table() -> List[Dict[str, Any]]:
    """Returns all deterministic clinical escalation rules."""
    from backend.rule_engine import get_rules_table as get_base_rules
    return get_base_rules()
