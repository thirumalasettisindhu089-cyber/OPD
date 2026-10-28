# Domain Primer: OPD Triage & Clinical Decision Support (H1)
**Talent AP Mega Hackathon 2026 — Problem H1: OPD Triage Assistant for an Overloaded Government Hospital**

---

## 1. Executive Summary & Clinical Setting
- **Hospital Context**: High-volume government district hospital OPD receiving ~800 walk-ins per day with only **2 attending physicians**.
- **Nurse Time Budget**: ≤ 60 seconds per patient at the triage desk.
- **Current Operational Failure**: First-Come-First-Served (FCFS) queueing. Patients with acute myocardial infarction (heart attack) or respiratory distress wait behind dozens of patients with mild viral fevers or routine repeat prescription requests.
- **Core Clinical Objective**: Rapidly, safely, and transparently stratify walk-in patients into 5 urgency levels, detect red-flag conditions, identify the correct clinical specialty department, and prevent catastrophic under-triage of true emergencies.

---

## 2. The 5-Level Triage Rubric (ESI-Adapted)

| Triage Level | Priority Name | Clinical Description | Maximum Safe Waiting Time | Clinical Resource Needs |
| :--- | :--- | :--- | :--- | :--- |
| **Level 1** | **Resuscitation / Immediate** | Immediately life-threatening; profound hemodynamic collapse, airway/breathing failure, cardiac arrest, coma. | **0 minutes (Immediate)** | Continuous physician presence, advanced resuscitation, airway/IV access. |
| **Level 2** | **Emergent / Very Urgent** | High risk, severe pain/distress, acute chest pain, altered mental state, severe dyspnea, stroke signs, septic shock risk. | **< 15 minutes** | Multiple urgent resources, continuous monitoring, immediate physician evaluation. |
| **Level 3** | **Urgent** | Stable vital signs but requires complex workup (2+ diagnostic or therapeutic resources, e.g., IV meds + labs + X-ray). | **< 60 minutes** | Two or more resources (e.g. labs, radiography, IV fluids). |
| **Level 4** | **Less Urgent** | Stable, single resource required (e.g., simple laceration suture, single X-ray for isolated extremity injury, oral antibiotics). | **< 120 minutes** | Exactly one diagnostic or therapeutic resource. |
| **Level 5** | **Non-Urgent** | Minimal or no resource required; routine medication refills, suture removal, chronic mild rash, mild viral cold. | **Up to 240 minutes** | Zero hospital resources beyond physical exam and oral prescription. |

---

## 3. Vital Sign Reference Ranges & Thresholds

### 3.1 Adult Thresholds (Age ≥ 12)
| Vital Sign | Normal Range | Critical / Level 1 (Resuscitation) | Emergent / Level 2 (High Risk) | Impossible / Missing Flag |
| :--- | :--- | :--- | :--- | :--- |
| **Systolic BP (SBP)** | 100 - 139 mmHg | < 70 mmHg (Profound shock) | 70 - 89 mmHg OR ≥ 200 mmHg | ≤ 40 or > 260 mmHg (0 = Sensor fault) |
| **Diastolic BP (DBP)**| 60 - 89 mmHg | < 40 mmHg | < 50 mmHg OR ≥ 120 mmHg | ≤ 30 or > 160 mmHg |
| **Heart Rate (HR)** | 60 - 99 bpm | < 40 bpm or > 160 bpm | 40 - 49 bpm OR 125 - 160 bpm | ≤ 25 or > 250 bpm |
| **Respiratory Rate (RR)**| 12 - 20 bpm | < 8 or > 38 bpm (Impending arrest) | 28 - 38 bpm | ≤ 4 or > 70 bpm |
| **SpO2 (Pulse Ox)** | 95 - 100% | < 85% (Severe hypoxia) | 85 - 89% | > 100% (Physics error) or ≤ 40% |
| **Temperature** | 36.5 - 37.5 °C | Severe hypothermia < 32.0 °C | Hyperpyrexia > 40.0 °C (> 104°F) | > 45.0 °C in Celsius box (= Fahrenheit entry!) |

### 3.2 Pediatric Protocol Bypass (Age < 12)
- Pediatric physiological ranges vary drastically by age group (infants, toddlers, school-age).
- **Rule Engine Mandate**: When `age < 12`, adult vital sign rules are **BYPASSED**, and the system outputs an explicit alert:
  > *"PEDIATRIC PATIENT: Adult vital sign cutoffs bypassed. Nurse must apply pediatric PALS/Broselow triage protocol."*

---

## 4. Multilingual Red-Flag Symptoms & Negation Lexicon

### 4.1 Telugu Transliteration Dictionary
- `gunde noppi`, `gundelo noppi`, `gunde potu`, `gundelo manta`: Chest pain / angina
- `aayasam`, `oopiri aadatledu`, `saas teesukovadam kashtam`, `saas aaguthondi`: Shortness of breath / dyspnea
- `kallu thiruguthunnayi`, `thala thiruguthundi`: Dizziness / vertigo / impending syncope
- `spruha tappipoyindi`, `padipoyadu`: Syncope / unconscious collapse
- `raktham paduthundi`, `raktham`: Bleeding / hemorrhage
- `vaanthulu`, `kadupu noppi`: Vomiting, severe abdominal pain
- `jwaram`, `teevramaina jwaram`: Fever, high fever
- `daggulu`: Cough
- **Telugu Negations**: `ledu`, `kaadu`, `raaledu`, `em ledu` (e.g., *"gunde noppi ledu"* = NO chest pain).

### 4.2 Hindi Transliteration Dictionary
- `chhati dard`, `chhati me dard`, `seene me dard`: Chest pain / angina
- `saas phool rahi hai`, `saas lene me takleef`, `dam ghut raha hai`: Severe shortness of breath
- `chakkar aana`, `chakkar aa rahe hai`, `behosh`, `gash khaa ke gir gaya`: Dizziness / syncope / collapse
- `khoon ulti`, `khoon beh raha hai`: Hematemesis / active bleeding
- `tez bukhar`: High fever
- `pet dard`: Abdominal pain
- `khansi`: Cough
- **Hindi Negations**: `nahi`, `nahin`, `nhi`, `nahi hai` (e.g., *"chhati me dard nahi hai"* = NO chest pain).

### 4.3 English Negation Modifiers
- `no`, `not`, `denies`, `without`, `free of`, `negative for`, `ruled out`, `never had`
- Window: 3 tokens before or after symptom word.

---

## 5. Asymmetric Cost Matrix & Evaluation Metric
In medical triage, errors are fundamentally asymmetric:
- **Under-triaging** a true emergency (predicting Level 4 or 5 for an acute Level 1 or 2 condition) leads to cardiac arrest or death in the waiting room. Penalty weight is **massive (~20x-50x)**.
- **Over-triaging** a mild case (predicting Level 2 for a common cold) causes minor resource consumption and queue delay. Penalty weight is **minimal (~1x-4x)**.
- **Abstention**: When the model is uncertain, missing critical data, or encounters gibberish, it outputs `"CANNOT ASSESS - SEND TO NURSE NOW"`. Appropriate abstention incurs a low, capped cost, protecting patient safety.

---

## 6. Target Clinical Departments
1. **Emergency / Cardiology**: Acute chest pain, cardiac arrest, arrhythmias, severe shock.
2. **Pulmonology**: Severe asthma, COPD exacerbation, acute respiratory distress, severe cough with hypoxia.
3. **General Medicine**: Fevers, infections, diabetes, hypertension management, weakness, general malaise.
4. **General Surgery / Emergency Surgery**: Acute abdomen, trauma, open wounds, appendicitis suspicion.
5. **Orthopedics**: Bone fractures, joint dislocations, sprains, musculoskeletal trauma.
6. **Pediatrics**: All non-trauma pediatric walk-ins under age 12.
7. **Obstetrics & Gynecology (OB/GYN)**: Pregnancy complaints, labor pains, vaginal bleeding.
8. **Neurology**: Stroke symptoms, seizures, sudden loss of consciousness, focal weakness.
9. **ENT (Ear, Nose, Throat)**: Epistaxis, acute ear infections, foreign body in throat/nose.
10. **Dermatology**: Rashes, skin lesions, superficial allergies without airway compromise.

