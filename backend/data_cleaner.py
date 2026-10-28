"""
backend/data_cleaner.py - Intelligent Intake Preprocessing & Clinical Sanitization
SmartTriage AI - Talent AP Mega Hackathon 2026

Handles:
1. Column alias resolution from varied CSV/intake headers
2. Impossible vitals detection (BP 0, SpO2 > 100%, Temp > 45 C) with explicit missing flags
3. Automatic Fahrenheit-in-Celsius-box detection and conversion
4. Text normalization: lowercasing, collapsing repeated characters, stripping artifacts
5. Generates nurse warnings and explainability flags
"""

import re
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from backend.config import COLUMN_ALIASES, VITALS_THRESHOLDS


def normalize_column_name(raw_name: str) -> str:
    """Finds canonical column name using COLUMN_ALIASES."""
    clean = raw_name.strip().lower().replace(" ", "_").replace("-", "_")
    for canonical, aliases in COLUMN_ALIASES.items():
        if clean == canonical or clean in aliases:
            return canonical
    return clean


def remap_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remaps all columns in a DataFrame according to the alias table."""
    rename_map = {}
    for col in df.columns:
        canonical = normalize_column_name(col)
        rename_map[col] = canonical
    return df.rename(columns=rename_map)


def collapse_repeated_characters(text: str) -> str:
    """
    Collapses 3 or more repeated letters to maximum 2, then normalizes common patterns.
    e.g. 'heaaadacheee' -> 'headache', 'paaaain' -> 'pain', 'severrrrre' -> 'severe'.
    """
    # Replace 3 or more consecutive identical characters with 1
    # For instance 'paaaain' -> 'pain', 'vomttting' -> 'vomiting'
    text = re.sub(r"([a-zA-Z])\1{2,}", r"\1", text)
    # Common medical typo normalizations
    typo_map = {
        r"\bpaain\b": "pain",
        r"\bheadaache\b": "headache",
        r"\bfeever\b": "fever",
        r"\bcouugh\b": "cough",
        r"\bvomtings\b": "vomiting",
        r"\bvomitting\b": "vomiting",
        r"\bbreathingg\b": "breathing",
        r"\bchestt\b": "chest",
        r"\bdiabeetes\b": "diabetes",
        r"\bhypertention\b": "hypertension",
    }
    for pattern, replacement in typo_map.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def clean_text_complaint(text: Optional[str]) -> str:
    """Normalizes complaint text for ML and Rule Engine analysis."""
    if text is None or pd.isna(text):
        return ""
    
    text = str(text).lower().strip()
    text = collapse_repeated_characters(text)
    # Remove excessive punctuation but keep words and letters
    text = re.sub(r"[^\w\s\-,/]", " ", text)
    # Collapse multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def sanitize_vitals(raw_vitals: Dict[str, Any]) -> Tuple[Dict[str, Optional[float]], Dict[str, bool], List[str]]:
    """
    Sanitizes vital signs.
    Treats impossible vitals as MISSING with a boolean flag, NEVER as normal.
    Detects Fahrenheit typed in a Celsius box.
    """
    cleaned_vitals: Dict[str, Optional[float]] = {}
    flags: Dict[str, bool] = {
        "bp_systolic_missing": False,
        "bp_systolic_impossible": False,
        "bp_diastolic_missing": False,
        "bp_diastolic_impossible": False,
        "heart_rate_missing": False,
        "heart_rate_impossible": False,
        "respiratory_rate_missing": False,
        "respiratory_rate_impossible": False,
        "temperature_missing": False,
        "temperature_impossible": False,
        "temp_fahrenheit_corrected": False,
        "spo2_missing": False,
        "spo2_impossible": False,
    }
    warnings: List[str] = []

    vt = VITALS_THRESHOLDS

    # 1. Systolic Blood Pressure
    sbp_raw = raw_vitals.get("bp_systolic")
    if sbp_raw is None or pd.isna(sbp_raw) or sbp_raw == "":
        cleaned_vitals["bp_systolic"] = None
        flags["bp_systolic_missing"] = True
    else:
        try:
            sbp = float(sbp_raw)
            if sbp <= 0:
                cleaned_vitals["bp_systolic"] = None
                flags["bp_systolic_missing"] = True
                flags["bp_systolic_impossible"] = True
                warnings.append("Systolic BP is 0 mmHg (sensor unattached or unrecorded) - treated as MISSING.")
            elif sbp < vt["bp_systolic"]["min_possible"] or sbp > vt["bp_systolic"]["max_possible"]:
                cleaned_vitals["bp_systolic"] = None
                flags["bp_systolic_missing"] = True
                flags["bp_systolic_impossible"] = True
                warnings.append(f"Systolic BP {sbp} mmHg is clinically impossible (<40 or >260) - treated as MISSING.")
            else:
                cleaned_vitals["bp_systolic"] = sbp
        except (ValueError, TypeError):
            cleaned_vitals["bp_systolic"] = None
            flags["bp_systolic_missing"] = True

    # 2. Diastolic Blood Pressure
    dbp_raw = raw_vitals.get("bp_diastolic")
    if dbp_raw is None or pd.isna(dbp_raw) or dbp_raw == "":
        cleaned_vitals["bp_diastolic"] = None
        flags["bp_diastolic_missing"] = True
    else:
        try:
            dbp = float(dbp_raw)
            if dbp <= 0:
                cleaned_vitals["bp_diastolic"] = None
                flags["bp_diastolic_missing"] = True
                flags["bp_diastolic_impossible"] = True
                warnings.append("Diastolic BP is 0 mmHg - treated as MISSING.")
            elif dbp < vt["bp_diastolic"]["min_possible"] or dbp > vt["bp_diastolic"]["max_possible"]:
                cleaned_vitals["bp_diastolic"] = None
                flags["bp_diastolic_missing"] = True
                flags["bp_diastolic_impossible"] = True
                warnings.append(f"Diastolic BP {dbp} mmHg is impossible (<30 or >160) - treated as MISSING.")
            else:
                cleaned_vitals["bp_diastolic"] = dbp
        except (ValueError, TypeError):
            cleaned_vitals["bp_diastolic"] = None
            flags["bp_diastolic_missing"] = True

    # 3. Heart Rate
    hr_raw = raw_vitals.get("heart_rate")
    if hr_raw is None or pd.isna(hr_raw) or hr_raw == "":
        cleaned_vitals["heart_rate"] = None
        flags["heart_rate_missing"] = True
    else:
        try:
            hr = float(hr_raw)
            if hr < vt["heart_rate"]["min_possible"] or hr > vt["heart_rate"]["max_possible"]:
                cleaned_vitals["heart_rate"] = None
                flags["heart_rate_missing"] = True
                flags["heart_rate_impossible"] = True
                warnings.append(f"Heart rate {hr} bpm is clinically impossible - treated as MISSING.")
            else:
                cleaned_vitals["heart_rate"] = hr
        except (ValueError, TypeError):
            cleaned_vitals["heart_rate"] = None
            flags["heart_rate_missing"] = True

    # 4. Respiratory Rate
    rr_raw = raw_vitals.get("respiratory_rate")
    if rr_raw is None or pd.isna(rr_raw) or rr_raw == "":
        cleaned_vitals["respiratory_rate"] = None
        flags["respiratory_rate_missing"] = True
    else:
        try:
            rr = float(rr_raw)
            if rr < vt["respiratory_rate"]["min_possible"] or rr > vt["respiratory_rate"]["max_possible"]:
                cleaned_vitals["respiratory_rate"] = None
                flags["respiratory_rate_missing"] = True
                flags["respiratory_rate_impossible"] = True
                warnings.append(f"Respiratory rate {rr} bpm is clinically impossible - treated as MISSING.")
            else:
                cleaned_vitals["respiratory_rate"] = rr
        except (ValueError, TypeError):
            cleaned_vitals["respiratory_rate"] = None
            flags["respiratory_rate_missing"] = True

    # 5. Temperature (°C or auto-detected °F in °C box)
    temp_raw = raw_vitals.get("temperature")
    if temp_raw is None or pd.isna(temp_raw) or temp_raw == "":
        cleaned_vitals["temperature"] = None
        flags["temperature_missing"] = True
    else:
        try:
            temp = float(temp_raw)
            # Detect Fahrenheit entered into Celsius box
            if temp >= vt["temperature_c"]["fahrenheit_detection_cutoff"]:
                # Value is in Fahrenheit! (e.g. 96 to 106 F)
                # Formula: (F - 32) * 5 / 9
                temp_c = round((temp - 32.0) * 5.0 / 9.0, 1)
                flags["temp_fahrenheit_corrected"] = True
                warnings.append(
                    f"Temperature {temp:.1f}° was entered in Celsius field: detected as FAHRENHEIT and auto-converted to {temp_c:.1f}°C."
                )
                if temp_c < vt["temperature_c"]["min_possible"] or temp_c > vt["temperature_c"]["max_possible"]:
                    cleaned_vitals["temperature"] = None
                    flags["temperature_missing"] = True
                    flags["temperature_impossible"] = True
                    warnings.append(f"Converted temperature {temp_c:.1f}°C is still out of viable biological range.")
                else:
                    cleaned_vitals["temperature"] = temp_c
            elif temp < vt["temperature_c"]["min_possible"] or temp > vt["temperature_c"]["max_possible"]:
                cleaned_vitals["temperature"] = None
                flags["temperature_missing"] = True
                flags["temperature_impossible"] = True
                warnings.append(f"Temperature {temp:.1f}°C is clinically impossible - treated as MISSING.")
            else:
                cleaned_vitals["temperature"] = round(temp, 1)
        except (ValueError, TypeError):
            cleaned_vitals["temperature"] = None
            flags["temperature_missing"] = True

    # 6. SpO2 (Pulse Oximetry)
    spo2_raw = raw_vitals.get("spo2")
    if spo2_raw is None or pd.isna(spo2_raw) or spo2_raw == "":
        cleaned_vitals["spo2"] = None
        flags["spo2_missing"] = True
    else:
        try:
            spo2 = float(spo2_raw)
            if spo2 > 100.0:
                cleaned_vitals["spo2"] = None
                flags["spo2_missing"] = True
                flags["spo2_impossible"] = True
                warnings.append(f"SpO2 {spo2}% is physically impossible (>100%) - treated as MISSING.")
            elif spo2 < vt["spo2"]["min_possible"]:
                cleaned_vitals["spo2"] = None
                flags["spo2_missing"] = True
                flags["spo2_impossible"] = True
                warnings.append(f"SpO2 {spo2}% is below biological survival threshold (<40%) - treated as MISSING.")
            else:
                cleaned_vitals["spo2"] = round(spo2, 1)
        except (ValueError, TypeError):
            cleaned_vitals["spo2"] = None
            flags["spo2_missing"] = True

    return cleaned_vitals, flags, warnings


def clean_patient_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main intake pipeline for a single patient record.
    Returns cleaned canonical representation with indicators, flags, and warnings.
    """
    # 1. Remap aliases
    canonical_dict = {}
    for k, v in raw_record.items():
        canonical_k = normalize_column_name(k)
        canonical_dict[canonical_k] = v

    # 2. Extract demographics
    age = canonical_dict.get("age")
    try:
        age = int(age) if age is not None and not pd.isna(age) else 35
    except (ValueError, TypeError):
        age = 35

    sex = str(canonical_dict.get("sex", "M")).strip().upper()
    if sex not in ["M", "F", "OTHER"]:
        sex = "M"

    # 3. Clean complaint text
    raw_complaint = canonical_dict.get("chief_complaint", "")
    clean_complaint = clean_text_complaint(raw_complaint)

    # 4. Clean conditions & medications
    conditions = str(canonical_dict.get("known_conditions", "None")).strip()
    if pd.isna(conditions) or conditions == "" or conditions.lower() == "nan":
        conditions = "None"

    meds = str(canonical_dict.get("current_medications", "None")).strip()
    if pd.isna(meds) or meds == "" or meds.lower() == "nan":
        meds = "None"

    # 5. Sanitize vitals
    cleaned_vitals, flags, warnings = sanitize_vitals(canonical_dict)

    # Determine pediatric status
    is_pediatric = (age < VITALS_THRESHOLDS["adult_age_cutoff"])

    return {
        "patient_id": canonical_dict.get("patient_id", "WALK_IN"),
        "age": age,
        "sex": sex,
        "is_pediatric": is_pediatric,
        "chief_complaint": clean_complaint,
        "raw_complaint": raw_complaint,
        "known_conditions": conditions,
        "current_medications": meds,
        **cleaned_vitals,
        "flags": flags,
        "warnings": warnings,
        # Preserve ground truth if present
        "triage_level": canonical_dict.get("triage_level"),
        "recommended_department": canonical_dict.get("recommended_department"),
        "true_emergency": canonical_dict.get("true_emergency"),
    }
