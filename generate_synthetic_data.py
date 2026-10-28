"""
generate_synthetic_data.py - Realistic OPD Triage & Arrival Log Generator
Talent AP Mega Hackathon 2026 - Problem H1: OPD Triage Assistant

Generates:
1. 30,000 synthetic patient intake records (and configurable sample sizes)
   - Realistic demographic distributions (adults, elderly, pediatric < 12)
   - Vitals with clinical correlation, sensor dropouts, 0 BP, SpO2 > 100%, and Fahrenheit entered in Celsius box
   - Multilingual chief complaints in English, transliterated Telugu, transliterated Hindi, and code-mixed formats
   - Realistic negation examples ("no chest pain", "chhati me dard nahi hai", "gunde noppi ledu")
   - Red flags, known comorbidities, medications
   - True emergency flag (~4% true emergencies as per hackathon specification)
   - Ground truth 5-level triage and specialty department
2. 800 walk-ins/day arrival log with peak surge hours and service durations for queue simulation
"""

import os
import random
import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Seed for reproducibility
random.seed(42)
np.random.seed(42)

# Medical departments
DEPARTMENTS = [
    "Emergency / Cardiology",
    "Pulmonology",
    "General Medicine",
    "General Surgery",
    "Orthopedics",
    "Pediatrics",
    "Obstetrics & Gynecology",
    "Neurology",
    "ENT",
    "Dermatology",
]

# Multilingual Complaints Library
# Format: (Text, Likely Level, Recommended Department, Red Flag Symptom Flag, Is Emergency)
COMPLAINT_TEMPLATES = [
    # Level 1: Resuscitation / Immediate (~1.5%)
    ("severe crushing chest pain radiating to left jaw, diaphoresis and gasping", 1, "Emergency / Cardiology", True, 1),
    ("gunde lo teevramaina noppi, oopiri aadatledu, spruha tappipotondi", 1, "Emergency / Cardiology", True, 1),
    ("chhati me behad tez dard, pasina chhoot raha hai, behosh ho gaya", 1, "Emergency / Cardiology", True, 1),
    ("gasping for breath, blue lips, severe stridor unable to speak", 1, "Pulmonology", True, 1),
    ("aayasam aagadam ledu, pedavulu neelamga maarayi, spruha ledu", 1, "Pulmonology", True, 1),
    ("massive hematemesis, vomiting buckets of dark blood, collapsed in waiting hall", 1, "Emergency / Cardiology", True, 1),
    ("sudden right-sided paralysis, facial droop, completely unresponsive to voice", 1, "Neurology", True, 1),
    ("sudden severe allergic reaction after medication, tongue swelling, throat closing", 1, "Emergency / Cardiology", True, 1),
    
    # Level 2: Emergent / Very Urgent (~3.5%)
    ("substernal chest heaviness for 45 minutes with nausea and sweating", 2, "Emergency / Cardiology", True, 1),
    ("gunde noppi severe ga undi, eeda thammudu cheyyi laakkuntundi", 2, "Emergency / Cardiology", True, 1),
    ("chhati me dard ho raha hai kal raat se, jalan aur ghabrahat hai", 2, "Emergency / Cardiology", True, 1),
    ("acute shortness of breath with known asthma, inhaler not helping at all", 2, "Pulmonology", True, 1),
    ("saas lene me bahut takleef, asthma pump kaam nahi kar raha", 2, "Pulmonology", True, 1),
    ("aayasam ekkuva undi, asthama mandulu vesukunna taggaledu", 2, "Pulmonology", True, 1),
    ("high grade fever 104 F with severe neck stiffness and confusion", 2, "General Medicine", True, 1),
    ("sudden worst headache of life with blurred vision and persistent vomiting", 2, "Neurology", True, 1),
    ("thala cheelipoyela noppi, kallu sarigga kanipiyatledu, vaanthulu", 2, "Neurology", True, 1),
    ("sar me achanak bhyankar dard shuru hua, ulti ho rahi hai lagatar", 2, "Neurology", True, 1),
    ("acute severe lower right abdominal pain with rebound tenderness and high fever", 2, "General Surgery", True, 1),
    ("kadupu lo ghoramaina noppi, muttukuntene aravatam, vaanthulu", 2, "General Surgery", True, 1),
    ("pregnant 34 weeks, sudden heavy vaginal bleeding and severe abdominal cramps", 2, "Obstetrics & Gynecology", True, 1),
    ("open compound fracture of right tibia with visible bone and bleeding", 2, "Orthopedics", True, 1),

    # Negation Cases (Crucial for rule engine & model testing - NOT emergencies!)
    ("patient has knee pain, denies chest pain or shortness of breath", 4, "Orthopedics", False, 0),
    ("mild headache and cold for 3 days, no chest pain, no breathing problem", 5, "General Medicine", False, 0),
    ("mochula noppi undi kani gunde noppi ledu, aayasam em ledu", 4, "Orthopedics", False, 0),
    ("vomiting 2 times today, chhati me dard nahi hai, bukhar halka hai", 4, "General Medicine", False, 0),
    ("pet dard hai thoda sa, saas lene me koi takleef nahi hai", 4, "General Medicine", False, 0),
    ("ear pain since yesterday, denies shortness of breath, without fever", 4, "ENT", False, 0),
    ("regular bp tablet refill, no chest pain, no dizziness, feeling okay", 5, "General Medicine", False, 0),

    # Level 3: Urgent (~25%)
    ("moderate abdominal pain, nausea, low grade fever for 2 days", 3, "General Medicine", False, 0),
    ("kadupu noppi 2 rojula nunchi undi, aakali veyyatledu", 3, "General Medicine", False, 0),
    ("pet me dard hai do din se, dast lag gaye hai", 3, "General Medicine", False, 0),
    ("persistent productive cough with yellowish phlegm and moderate fever", 3, "Pulmonology", False, 0),
    ("daggulo thelupu kapharn paduthondi, jwaram taggaledu", 3, "Pulmonology", False, 0),
    ("khansi bahut hai balgam ke sath, pichhle 5 din se", 3, "Pulmonology", False, 0),
    ("twisted ankle while playing, swollen and inability to bear weight", 3, "Orthopedics", False, 0),
    ("kaalu madata padindi, vaapu vachindi nadavaleru", 3, "Orthopedics", False, 0),
    ("painful urination with flank pain and fever chills, suspect UTI", 3, "General Medicine", False, 0),
    ("mootram lo manta, nadumu noppi, vanukuthu jwaram", 3, "General Medicine", False, 0),
    ("peshab me jalan aur kamar me tez dard, bukhar", 3, "General Medicine", False, 0),
    ("uncontrolled high blood sugar reading at home 340 mg/dl, weakness", 3, "General Medicine", False, 0),
    ("diabetic patient with slow-healing foot ulcer and foul odor", 3, "General Surgery", False, 0),

    # Level 4: Less Urgent (~40%)
    ("simple superficial laceration on left forearm from kitchen knife, bleeding stopped", 4, "General Surgery", False, 0),
    ("cheyyi meeda koyyabaddadi, kottadam aagindi", 4, "General Surgery", False, 0),
    ("chaku se haath kat gaya halka sa, khoon band ho gaya", 4, "General Surgery", False, 0),
    ("ear pain and discharge for 3 days, mild hearing fullness", 4, "ENT", False, 0),
    ("chevi lo noppi, neellu kaaruthunnayi", 4, "ENT", False, 0),
    ("kaan me dard aur khujli ho rahi hai", 4, "ENT", False, 0),
    ("sore throat and painful swallowing with runny nose, no fever", 4, "ENT", False, 0),
    ("gontu noppi, mingatam kashtam, jwaram ledu", 4, "ENT", False, 0),
    ("gale me kharash aur dard hai, thand lag gayi hai", 4, "ENT", False, 0),
    ("itchy erythematous skin rash on both arms after garden work", 4, "Dermatology", False, 0),
    ("chethula meeda durada ga undi, erraga kandindi", 4, "Dermatology", False, 0),
    ("chamdi pe lal daane aur khujli hai do din se", 4, "Dermatology", False, 0),
    ("chronic lower back pain aggravated by lifting groceries yesterday", 4, "Orthopedics", False, 0),
    ("nadumu noppi chaala kaalam nunchi undi, ninna baruvu ethithe ekkuvaindi", 4, "Orthopedics", False, 0),
    ("kamar me dard rehta hai, kal se thoda badh gaya", 4, "Orthopedics", False, 0),
    ("mild diarrhea 3 times today, drinking oral rehydration fluids", 4, "General Medicine", False, 0),
    ("diarrhea ayindi 3 sarlu, ors thaagutunna", 4, "General Medicine", False, 0),

    # Level 5: Non-urgent (~30%)
    ("routine follow-up for chronic hypertension, needs monthly prescription renewal", 5, "General Medicine", False, 0),
    ("bp tablets aipoyayi, monthly mandulu raayinchukodaniki vachanu", 5, "General Medicine", False, 0),
    ("sugar ki dawai khatam ho gayi hai, monthly parchi banwani hai", 5, "General Medicine", False, 0),
    ("mild runny nose and sneezing for 2 days, no fever, no cough", 5, "General Medicine", False, 0),
    ("jalubu matrame undi, jwaram ledu, normal ga unnanu", 5, "General Medicine", False, 0),
    ("halka jukam hai do din se, bukhar bilkul nahi", 5, "General Medicine", False, 0),
    ("came for suture removal on forehead, wound clean and dry", 5, "General Surgery", False, 0),
    ("kattulu vippinchukodaniki vachamu, gaayam aari poindi", 5, "General Surgery", False, 0),
    ("taanke katwane aaye hai, ghaav sookh gaya hai", 5, "General Surgery", False, 0),
    ("mild dandruff and scalp itching for 2 weeks", 5, "Dermatology", False, 0),
    ("talalo tarumu, durada matrame undi", 5, "Dermatology", False, 0),
    ("sir me rusi aur khujli hai do hafte se", 5, "Dermatology", False, 0),
    ("medical fitness certificate needed for college admission", 5, "General Medicine", False, 0),
    ("college admission kosam fitness certificate kavali", 5, "General Medicine", False, 0),
    ("naukri ke liye medical fitness form sign karwana hai", 5, "General Medicine", False, 0),
]

# Chronic conditions pool
CHRONIC_CONDITIONS = [
    "None",
    "Hypertension",
    "Type 2 Diabetes Mellitus",
    "Hypertension, Type 2 Diabetes",
    "Asthma",
    "COPD",
    "Coronary Artery Disease, Prior MI",
    "Chronic Kidney Disease",
    "Hypothyroidism",
    "Epilepsy",
    "Rheumatoid Arthritis",
]

# Medications pool
MEDICATIONS_POOL = [
    "None",
    "Amlodipine 5mg",
    "Metformin 500mg, Glimepiride 1mg",
    "Telmisartan 40mg, Metformin 500mg",
    "Salbutamol Inhaler, Budecort Inhaler",
    "Aspirin 75mg, Atorvastatin 20mg",
    "Levothyroxine 50mcg",
    "Paracetamol as needed",
    "Pantoprazole 40mg",
    "Sodium Valproate 300mg",
]


def generate_vitals_for_level(level: int, age: int) -> dict:
    """Generates correlated physiological vitals with realistic medical noise & errors."""
    is_pediatric = (age < 12)
    
    # Base ranges according to triage level
    if level == 1:
        # Resuscitation: profound shock, extreme tachycardia/bradycardia, severe hypoxia
        systolic = np.random.choice([np.random.randint(50, 75), np.random.randint(210, 250)])
        diastolic = max(30, int(systolic * np.random.uniform(0.5, 0.65)))
        hr = np.random.choice([np.random.randint(35, 48), np.random.randint(145, 185)])
        rr = np.random.choice([np.random.randint(6, 9), np.random.randint(38, 50)])
        temp = round(float(np.random.choice([np.random.uniform(34.0, 35.5), np.random.uniform(38.0, 40.5)])), 1)
        spo2 = np.random.randint(72, 86)
    elif level == 2:
        # Emergent: hypotensive or severe hypertension, tachycardia, moderate hypoxia
        systolic = np.random.choice([np.random.randint(75, 89), np.random.randint(175, 205)])
        diastolic = max(45, int(systolic * np.random.uniform(0.55, 0.70)))
        hr = np.random.randint(115, 145)
        rr = np.random.randint(26, 36)
        temp = round(float(np.random.uniform(37.0, 40.2)), 1)
        spo2 = np.random.randint(87, 92)
    elif level == 3:
        # Urgent: borderline vitals, stable
        systolic = np.random.randint(95, 145)
        diastolic = np.random.randint(60, 92)
        hr = np.random.randint(80, 110)
        rr = np.random.randint(18, 26)
        temp = round(float(np.random.uniform(36.8, 38.8)), 1)
        spo2 = np.random.randint(93, 97)
    elif level == 4:
        # Less Urgent: normal vitals
        systolic = np.random.randint(110, 135)
        diastolic = np.random.randint(70, 85)
        hr = np.random.randint(65, 88)
        rr = np.random.randint(14, 20)
        temp = round(float(np.random.uniform(36.4, 37.4)), 1)
        spo2 = np.random.randint(96, 100)
    else:  # Level 5
        # Non-urgent: completely normal vitals
        systolic = np.random.randint(110, 130)
        diastolic = np.random.randint(70, 82)
        hr = np.random.randint(60, 82)
        rr = np.random.randint(12, 18)
        temp = round(float(np.random.uniform(36.5, 37.2)), 1)
        spo2 = np.random.randint(97, 100)

    # Pediatric baseline adjustments
    if is_pediatric:
        hr = int(hr * 1.3)  # Normal infant/child HR is higher
        rr = int(rr * 1.3)
        systolic = int(systolic * 0.85)

    # Introduce realistic real-world errors (~5% noise probability)
    roll = random.random()
    if roll < 0.015:
        # Sensor unreadable / blood pressure 0
        systolic = 0
        diastolic = 0
    elif roll < 0.030:
        # Fahrenheit entered in Celsius box! (e.g. 98.6 to 103.5 C)
        temp = round(float(np.random.uniform(97.5, 103.5)), 1)
    elif roll < 0.040:
        # SpO2 artifact error (> 100%)
        spo2 = np.random.choice([102, 105, 999])
    elif roll < 0.050:
        # Temperature 96 C typed in (classic hackathon prompt case)
        temp = 96.0

    return {
        "bp_systolic": systolic,
        "bp_diastolic": diastolic,
        "heart_rate": hr,
        "respiratory_rate": rr,
        "temperature_c": temp,
        "spo2": spo2,
    }


def generate_dataset(n_samples: int = 30000) -> pd.DataFrame:
    """Generates the main OPD triage dataset."""
    records = []
    
    # Distribution of levels:
    # Level 1: ~1.5%
    # Level 2: ~3.5% (Total True Emergencies Level 1 + 2 = ~5%)
    # Level 3: ~25%
    # Level 4: ~40%
    # Level 5: ~30%
    level_weights = [0.015, 0.035, 0.25, 0.40, 0.30]

    templates_by_level = {lvl: [t for t in COMPLAINT_TEMPLATES if t[1] == lvl] for lvl in range(1, 6)}

    for i in range(n_samples):
        patient_id = f"P{100000 + i + 1}"
        
        # Age distribution: 8% pediatric (<12), 70% adult (12-64), 22% elderly (65-90)
        age_cohort = np.random.choice(["pediatric", "adult", "elderly"], p=[0.08, 0.70, 0.22])
        if age_cohort == "pediatric":
            age = int(np.random.randint(1, 12))
        elif age_cohort == "adult":
            age = int(np.random.randint(12, 65))
        else:
            age = int(np.random.randint(65, 92))

        sex = np.random.choice(["M", "F"], p=[0.51, 0.49])

        # Pick target triage level
        assigned_level = int(np.random.choice([1, 2, 3, 4, 5], p=level_weights))
        
        # Pick complaint template
        tpl = random.choice(templates_by_level[assigned_level])
        complaint_text, ground_truth_level, dept, has_red_flag, is_emergency = tpl

        # If pediatric patient and non-emergency, assign to Pediatrics department
        if age < 12 and ground_truth_level not in [1, 2]:
            dept = "Pediatrics"

        # Occasional typographical jitter (simulating nurse speed typing)
        if random.random() < 0.15:
            complaint_text = complaint_text.replace("pain", "paain").replace("fever", "feever").replace("cough", "couugh")

        # Generate vitals
        vitals = generate_vitals_for_level(ground_truth_level, age)

        # Pick conditions & medications
        conditions = random.choice(CHRONIC_CONDITIONS)
        meds = random.choice(MEDICATIONS_POOL) if conditions != "None" else "None"

        records.append({
            "patient_id": patient_id,
            "age": age,
            "sex": sex,
            "chief_complaint": complaint_text,
            "bp_systolic": vitals["bp_systolic"],
            "bp_diastolic": vitals["bp_diastolic"],
            "heart_rate": vitals["heart_rate"],
            "respiratory_rate": vitals["respiratory_rate"],
            "temperature": vitals["temperature_c"],
            "spo2": vitals["spo2"],
            "known_conditions": conditions,
            "current_medications": meds,
            "triage_level": ground_truth_level,
            "recommended_department": dept,
            "true_emergency": is_emergency,
        })

    df = pd.DataFrame(records)
    return df


def generate_arrival_log(n_patients: int = 800) -> pd.DataFrame:
    """
    Generates realistic 800 walk-ins/day arrival log for queue simulation.
    OPD shift: 08:00 to 16:00 (8 hours).
    Arrival surge peaks around 09:00 - 11:30 AM.
    """
    start_time = datetime(2026, 4, 18, 8, 0, 0)
    total_minutes = 8 * 60  # 480 minutes

    # Bimodal Gaussian arrival curve (Morning peak at 9:30 AM, secondary at 12:30 PM)
    arrivals_m = []
    for _ in range(n_patients):
        if random.random() < 0.70:
            m = np.random.normal(loc=90, scale=45)  # Peak around 9:30 AM
        else:
            m = np.random.normal(loc=270, scale=60) # Afternoon
        m = max(0, min(total_minutes - 5, m))
        arrivals_m.append(m)

    arrivals_m.sort()

    records = []
    level_weights = [0.015, 0.035, 0.25, 0.40, 0.30]
    
    # Required physician consultation duration (minutes) by triage level
    consult_time_map = {
        1: 20.0,  # Resuscitation (needs heavy physician intervention)
        2: 15.0,  # Emergent workup
        3: 10.0,  # Urgent
        4: 6.0,   # Less urgent
        5: 4.0,   # Non-urgent prescription renewal
    }

    for idx, arr_m in enumerate(arrivals_m):
        arr_dt = start_time + timedelta(minutes=float(arr_m))
        patient_id = f"WALK_{1001 + idx}"
        age = int(np.random.randint(5, 82))
        level = int(np.random.choice([1, 2, 3, 4, 5], p=level_weights))
        service_duration = round(float(np.random.normal(consult_time_map[level], 1.5)), 1)
        service_duration = max(2.0, service_duration)

        records.append({
            "patient_id": patient_id,
            "arrival_time": arr_dt.strftime("%H:%M:%S"),
            "arrival_minute": round(float(arr_m), 1),
            "age": age,
            "triage_level": level,
            "service_duration_min": service_duration,
        })

    return pd.DataFrame(records)


def main():
    parser = argparse.ArgumentParser(description="SmartTriage Synthetic Data Generator")
    parser.add_argument("--samples", type=int, default=30000, help="Number of triage intake records")
    parser.add_argument("--arrivals", type=int, default=800, help="Number of arrival walk-ins")
    parser.add_argument("--out-dir", type=str, default="data", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    print(f"[*] Generating {args.samples:,} synthetic OPD intake records...")
    df_triage = generate_dataset(args.samples)
    triage_path = os.path.join(args.out_dir, "dataset.csv")
    df_triage.to_csv(triage_path, index=False)
    print(f"[+] Saved triage dataset: {triage_path} ({len(df_triage):,} records)")

    print(f"[*] Generating {args.arrivals} walk-ins arrival log (2-doctor shift)...")
    df_arrivals = generate_arrival_log(args.arrivals)
    arrival_path = os.path.join(args.out_dir, "arrival_log.csv")
    df_arrivals.to_csv(arrival_path, index=False)
    print(f"[+] Saved arrival log: {arrival_path} ({len(df_arrivals):,} records)")

    # Print summary statistics
    emergencies = df_triage['true_emergency'].sum()
    print("-" * 60)
    print(f"Dataset Level Distribution:\n{df_triage['triage_level'].value_counts(normalize=True).sort_index() * 100}")
    print(f"Total True Emergencies: {emergencies:,} ({emergencies/len(df_triage)*100:.2f}%)")
    print("-" * 60)


if __name__ == "__main__":
    main()
