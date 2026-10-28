"""
backend/config.py - Clinical Configuration, Alias Mappings, and Thresholds
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

import numpy as np

# Column aliases for flexible CSV intake mapping
COLUMN_ALIASES = {
    "patient_id": ["patient_id", "pid", "id", "mrn", "patient_no", "reg_no"],
    "age": ["age", "patient_age", "age_years", "age_yrs", "pt_age"],
    "sex": ["sex", "gender", "patient_sex", "pt_gender"],
    "chief_complaint": [
        "chief_complaint", "complaint", "symptoms", "cc", "presenting_complaint",
        "reason_for_visit", "complaints", "patient_complaint", "history"
    ],
    "bp_systolic": ["bp_systolic", "systolic", "sys_bp", "bp_sys", "systolic_bp", "sbp", "sys"],
    "bp_diastolic": ["bp_diastolic", "diastolic", "dia_bp", "bp_dia", "diastolic_bp", "dbp", "dia"],
    "heart_rate": ["heart_rate", "pulse", "hr", "pulse_rate", "pr", "bpm"],
    "respiratory_rate": ["respiratory_rate", "resp_rate", "rr", "breaths_per_min", "resp"],
    "temperature": ["temperature", "temp", "body_temp", "temp_c", "temp_f", "temperature_c"],
    "spo2": ["spo2", "o2_sat", "oxygen_saturation", "pulse_ox", "sat", "o2sat"],
    "known_conditions": ["known_conditions", "conditions", "past_medical_history", "pmh", "comorbidities", "history_of"],
    "current_medications": ["current_medications", "medications", "meds", "current_meds", "rx", "drug_history"],
    "triage_level": ["triage_level", "level", "esi_level", "priority", "target_level", "ground_truth_level"],
    "recommended_department": ["recommended_department", "department", "dept", "recommended_dept", "target_department"],
    "true_emergency": ["true_emergency", "is_emergency", "emergency_flag", "emergency"],
}

# Plausible and Critical Physiological Ranges
# Anything outside IMPOSSIBLE thresholds is flagged as missing/sensor failure
VITALS_THRESHOLDS = {
    "adult_age_cutoff": 12,  # Patients < 12 years are classified as pediatric
    "bp_systolic": {
        "min_possible": 40,
        "max_possible": 260,
        "critical_low_l1": 70,   # Profound shock -> Level 1
        "emergent_low_l2": 90,   # Hypotension -> Level 2
        "emergent_high_l2": 200, # Hypertensive crisis -> Level 2
    },
    "bp_diastolic": {
        "min_possible": 30,
        "max_possible": 160,
        "critical_low_l1": 40,
        "emergent_low_l2": 50,
        "emergent_high_l2": 120,
    },
    "heart_rate": {
        "min_possible": 25,
        "max_possible": 250,
        "critical_low_l1": 40,   # Severe bradycardia -> Level 1
        "critical_high_l1": 160, # Extreme tachycardia -> Level 1
        "emergent_high_l2": 125, # High tachycardia -> Level 2
    },
    "respiratory_rate": {
        "min_possible": 4,
        "max_possible": 70,
        "critical_low_l1": 8,    # Impending respiratory arrest -> Level 1
        "critical_high_l1": 38,  # Severe tachypnea -> Level 1
        "emergent_high_l2": 28,  # Acute respiratory distress -> Level 2
    },
    "spo2": {
        "min_possible": 40,
        "max_possible": 100,     # SpO2 > 100% is physically impossible sensor artifact
        "critical_low_l1": 85,   # Severe hypoxia -> Level 1
        "emergent_low_l2": 90,   # Hypoxia -> Level 2
    },
    "temperature_c": {
        "min_possible": 30.0,
        "max_possible": 43.5,
        "fahrenheit_detection_cutoff": 45.0, # Values > 45 C are assumed to be Fahrenheit entered by nurse
        "critical_hypothermia_l1": 32.0,
        "emergent_hyperpyrexia_l2": 40.0,    # > 104 F with tachycardia
    }
}

# Multilingual Red-Flag Symptoms (English, Transliterated Telugu, Transliterated Hindi)
RED_FLAG_PATTERNS = {
    "cardiac": {
        "keywords": [
            "chest pain", "crushing pain", "substernal", "radiating to arm", "jaw pain", "angina",
            # Telugu transliterated
            "gunde noppi", "gundelo noppi", "gunde potu", "gunde lo manta", "gundelo manta", "gunde baadha",
            # Hindi transliterated
            "chhati dard", "chhati me dard", "seene me dard", "chhati jalan", "chhati bhari"
        ],
        "default_level": 2,
        "department": "Emergency / Cardiology",
        "description": "Suspected acute coronary syndrome (ACS) / myocardial infarction"
    },
    "respiratory": {
        "keywords": [
            "shortness of breath", "gasping", "stridor", "blue lips", "cyanosis", "unable to breathe",
            "severe asthma", "respiratory distress",
            # Telugu transliterated
            "aayasam", "oopiri aadatledu", "saas aaguthondi", "saas teesukovadam kashtam", "dammu",
            # Hindi transliterated
            "saas phool", "saas lene me takleef", "dam ghut raha", "saans nahi", "dam ghutan"
        ],
        "default_level": 2,
        "department": "Pulmonology",
        "description": "Acute respiratory compromise / severe dyspnea"
    },
    "neurological": {
        "keywords": [
            "facial droop", "slurred speech", "one sided weakness", "hemiparesis", "unresponsive",
            "loss of consciousness", "syncope", "active seizure", "worst headache of life",
            # Telugu transliterated
            "spruha tappipoyindi", "kallu thirigi padipoyadu", "thala cheelipoyela", "vaakku padipoyindi",
            # Hindi transliterated
            "behosh", "chakkar aa ke gir", "muh tedha", "bol nahi pa raha", "dora padna"
        ],
        "default_level": 2,
        "department": "Neurology",
        "description": "Acute stroke / neurological emergency / altered mental state"
    },
    "hemorrhage": {
        "keywords": [
            "vomiting blood", "hematemesis", "coughing blood", "hemoptysis", "massive bleeding",
            "uncontrolled bleeding", "compound fracture",
            # Telugu transliterated
            "raktham paduthundi", "raktham ulti", "raktham aagatledu",
            # Hindi transliterated
            "khoon ulti", "khoon nikal raha hai", "khoon beh raha hai"
        ],
        "default_level": 2,
        "department": "Emergency / Cardiology",
        "description": "Active severe hemorrhage / hemodynamic collapse risk"
    },
    "anaphylaxis": {
        "keywords": [
            "throat closing", "tongue swelling", "lip swelling", "severe allergic reaction",
            "anaphylaxis", "gale me sujan"
        ],
        "default_level": 1,
        "department": "Emergency / Cardiology",
        "description": "Severe airway-compromising anaphylaxis"
    }
}

# Negation terms across English, Telugu, and Hindi
NEGATION_TERMS = {
    "en": ["no", "not", "denies", "without", "free of", "ruled out", "never had", "negative for"],
    "te": ["ledu", "kaadu", "raaledu", "em ledu", "undadu"],
    "hi": ["nahi", "nahin", "nhi", "nahi hai", "bilkul nahi", "mat"]
}

# Asymmetric Cost Matrix
ASYMMETRIC_COST_MATRIX = np.array([
    # Pred: L1   L2   L3   L4    L5
    [   0.0, 10.0, 35.0, 80.0, 150.0],  # True L1
    [   2.0,  0.0, 15.0, 45.0,  95.0],  # True L2
    [   5.0,  2.0,  0.0, 10.0,  30.0],  # True L3
    [   8.0,  3.0,  1.0,  0.0,   5.0],  # True L4
    [  10.0,  5.0,  2.0,  1.0,   0.0],  # True L5
], dtype=np.float64)

# Abstention Costs per True Level
ABSTENTION_COSTS = np.array([5.0, 4.0, 3.0, 2.0, 1.0], dtype=np.float64)

# Model Abstention Hyperparameters
CONFIDENCE_THRESHOLD = 0.40  # Max probability below this triggers abstention
MAX_ALLOWABLE_MISSING_VITALS = 3  # If >3 vitals missing and text is short, abstain
