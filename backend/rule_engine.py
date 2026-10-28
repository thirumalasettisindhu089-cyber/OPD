"""
backend/rule_engine.py - Pure Python Clinical Escalation & Rule Engine
SmartTriage AI - Talent AP Mega Hackathon 2026

Runs BEFORE the ML model and OVERRIDES it when pointing to higher urgency.
Guarantees emergency safety:
- Deterministic critical vital sign escalation (Adult Level 1 & Level 2)
- Pediatric protocol bypass (age < 12) with nurse advisory
- Multilingual red-flag symptom detection (English, Telugu, Hindi)
- Robust negation checking ("no chest pain", "chhati dard nahi", "gunde noppi ledu")
- Exposes structured rules table for transparency & regulatory audit
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from backend.config import VITALS_THRESHOLDS, RED_FLAG_PATTERNS, NEGATION_TERMS


def is_negated(text: str, match_start: int, match_end: int, window_chars: int = 35) -> bool:
    """
    Checks if a matched symptom in text is negated.
    Scans window before and after the match for English, Telugu, and Hindi negators.
    Example: 'patient has knee pain, denies chest pain' -> 'chest pain' is preceded by 'denies'.
    Example: 'gunde noppi ledu' -> 'gunde noppi' is followed by 'ledu'.
    Example: 'chhati me dard nahi hai' -> 'chhati me dard' is followed by 'nahi hai'.
    """
    start_window = max(0, match_start - window_chars)
    end_window = min(len(text), match_end + window_chars)

    pre_text = text[start_window:match_start].lower()
    post_text = text[match_end:end_window].lower()

    # Aggregate all negation tokens
    all_negators = (
        NEGATION_TERMS["en"] +
        NEGATION_TERMS["te"] +
        NEGATION_TERMS["hi"]
    )

    # Check preceding tokens
    for neg in all_negators:
        # Preceding check: e.g. "no chest pain", "denies chest pain", "without pain"
        pattern_pre = r"\b" + re.escape(neg) + r"\b"
        if re.search(pattern_pre, pre_text):
            return True

        # Succeeding check: e.g. "gunde noppi ledu", "dard nahi hai"
        pattern_post = r"\b" + re.escape(neg) + r"\b"
        if re.search(pattern_post, post_text):
            return True

    return False


def detect_red_flags(clean_complaint: str) -> List[Dict[str, Any]]:
    """
    Detects multilingual red-flag symptoms in cleaned complaint text,
    verifying they are NOT negated.
    """
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
                    break  # One match per category is sufficient
    return detected


def evaluate_rules(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main Rule Engine evaluation.
    Evaluates vitals and red flags deterministically.
    Returns override decision, clinical rationale, and nurse advisories.
    """
    age = record.get("age", 35)
    is_pediatric = record.get("is_pediatric", age < 12)
    flags = record.get("flags", {})

    sbp = record.get("bp_systolic")
    dbp = record.get("bp_diastolic")
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

    # 1. PEDIATRIC PROTOCOL CHECK
    if is_pediatric:
        nurse_alerts.append(
            f"PEDIATRIC PATIENT (Age {age} < 12): Adult vital sign cutoffs bypassed. Apply pediatric PALS / Broselow protocol."
        )

    # 2. VITAL SIGNS RULES (Bypassed for pediatrics)
    if not is_pediatric:
        # --- Level 1 Resuscitation (Profound physiological failure) ---
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

        # --- Level 2 Emergent (Severe physiological derangement) ---
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

    # 3. RED-FLAG SYMPTOMS (Active for all patients, including pediatrics)
    red_flags = detect_red_flags(complaint)
    for rf in red_flags:
        rf_term = rf["matched_term"]
        rf_desc = rf["description"]
        rf_level = rf["default_level"]
        red_flag_chips.append(f"{rf['category'].upper()}: {rf_term}")

        # Check anaphylaxis
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

    # If any rule triggered, rule overrides the model
    rule_triggered = (rule_level is not None)

    return {
        "rule_triggered": rule_triggered,
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
    """Returns all deterministic rules in a structured table for UI and auditing."""
    return [
        {
            "id": "R01",
            "category": "Critical Vitals",
            "condition": "Systolic BP < 70 mmHg (Adult)",
            "urgency_level": "Level 1 (Resuscitation)",
            "action": "Force Level 1 & Emergency Dept",
            "rationale": "Profound hemodynamic shock / end-organ collapse risk"
        },
        {
            "id": "R02",
            "category": "Critical Vitals",
            "condition": "SpO2 < 85% on Room Air (Adult)",
            "urgency_level": "Level 1 (Resuscitation)",
            "action": "Force Level 1 & Pulmonology/Emergency",
            "rationale": "Severe life-threatening hypoxemia, impending respiratory arrest"
        },
        {
            "id": "R03",
            "category": "Critical Vitals",
            "condition": "Heart Rate < 40 or > 160 bpm (Adult)",
            "urgency_level": "Level 1 (Resuscitation)",
            "action": "Force Level 1 & Emergency Dept",
            "rationale": "Severe unstable bradyarrhythmia or tachyarrhythmia"
        },
        {
            "id": "R04",
            "category": "Critical Vitals",
            "condition": "Respiratory Rate < 8 or > 38 bpm (Adult)",
            "urgency_level": "Level 1 (Resuscitation)",
            "action": "Force Level 1 & Pulmonology/Emergency",
            "rationale": "Respiratory muscle fatigue, impending apnea"
        },
        {
            "id": "R05",
            "category": "Emergent Vitals",
            "condition": "Systolic BP 70-89 mmHg OR >= 200 mmHg",
            "urgency_level": "Level 2 (Emergent)",
            "action": "Force Level 2 & Emergency Dept",
            "rationale": "Hypoperfusion state or acute hypertensive emergency"
        },
        {
            "id": "R06",
            "category": "Emergent Vitals",
            "condition": "SpO2 85-89%",
            "urgency_level": "Level 2 (Emergent)",
            "action": "Force Level 2 & Pulmonology",
            "rationale": "Acute hypoxia requiring rapid supplemental oxygen therapy"
        },
        {
            "id": "R07",
            "category": "Emergent Vitals",
            "condition": "Heart Rate 125-160 bpm OR RR 28-38 bpm",
            "urgency_level": "Level 2 (Emergent)",
            "action": "Force Level 2",
            "rationale": "Severe compensatory physiological distress"
        },
        {
            "id": "R08",
            "category": "Emergent Vitals",
            "condition": "Temp >= 40.0°C (104°F) with HR > 100 bpm",
            "urgency_level": "Level 2 (Emergent)",
            "action": "Force Level 2 & General Medicine",
            "rationale": "Suspected severe systemic infection / early sepsis"
        },
        {
            "id": "R09",
            "category": "Red Flag Symptoms",
            "condition": "Acute chest pain / 'gunde noppi' / 'chhati dard' (un-negated)",
            "urgency_level": "Level 2 (Emergent)",
            "action": "Force Level 2 & Cardiology",
            "rationale": "Suspected Acute Coronary Syndrome (ACS) / Myocardial Infarction"
        },
        {
            "id": "R10",
            "category": "Red Flag Symptoms",
            "condition": "Severe dyspnea / 'aayasam' / 'saas phool' (un-negated)",
            "urgency_level": "Level 2 (Emergent)",
            "action": "Force Level 2 & Pulmonology",
            "rationale": "Acute bronchospasm, pulmonary edema, or severe asthma"
        },
        {
            "id": "R11",
            "category": "Red Flag Symptoms",
            "condition": "Stroke signs / sudden weakness / 'spruha tappipoyindi' / 'behosh'",
            "urgency_level": "Level 2 (Emergent)",
            "action": "Force Level 2 & Neurology",
            "rationale": "Time-critical ischemic stroke or intracranial pathology window"
        },
        {
            "id": "R12",
            "category": "Red Flag Symptoms",
            "condition": "Massive hemorrhage / 'raktham paduthundi' / 'khoon ulti'",
            "urgency_level": "Level 2 (Emergent)",
            "action": "Force Level 2 & Emergency/Surgery",
            "rationale": "Rapid blood loss leading to hypovolemic shock"
        },
        {
            "id": "R13",
            "category": "Red Flag Symptoms",
            "condition": "Tongue/throat swelling, severe allergic reaction",
            "urgency_level": "Level 1 (Resuscitation)",
            "action": "Force Level 1 & Emergency Dept",
            "rationale": "Acute life-threatening upper airway obstruction (anaphylaxis)"
        },
        {
            "id": "R14",
            "category": "Pediatric Protocol",
            "condition": "Patient Age < 12 years",
            "urgency_level": "Protocol Bypass Alert",
            "action": "Bypass adult vitals rules; Notify nurse",
            "rationale": "Pediatric vitals differ significantly by age cohort; nurse must use PALS rubric"
        },
        {
            "id": "R15",
            "category": "Negation Handling",
            "condition": "Red flag token preceded/followed by negator (e.g. 'no chest pain', 'gunde noppi ledu')",
            "urgency_level": "Negation Suppressed",
            "action": "Suppress red flag escalation",
            "rationale": "Prevents false-alarm queue clogging when patient explicitly denies emergency symptom"
        }
    ]
