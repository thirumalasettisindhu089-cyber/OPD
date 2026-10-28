"""
backend/app/schemas/triage.py - Pydantic Request & Response Schemas
SmartTriage AI - Talent AP Mega Hackathon 2026
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TriageRequest(BaseModel):
    patient_id: Optional[str] = Field(default="WALK_IN_01", description="Patient Identification Token")
    age: Optional[int] = Field(default=35, ge=0, le=120, description="Patient age in years (<12 triggers pediatric protocol)")
    sex: Optional[str] = Field(default="M", description="Sex: M, F, or OTHER")
    chief_complaint: str = Field(default="", description="Free text complaint in English, Telugu, Hindi transliteration")
    bp_systolic: Optional[float] = Field(default=None, description="Systolic Blood Pressure (mmHg)")
    bp_diastolic: Optional[float] = Field(default=None, description="Diastolic Blood Pressure (mmHg)")
    heart_rate: Optional[float] = Field(default=None, description="Heart rate / Pulse (bpm)")
    respiratory_rate: Optional[float] = Field(default=None, description="Respiratory rate (breaths/min)")
    temperature: Optional[float] = Field(default=None, description="Body Temperature (°C field, auto-converts °F)")
    spo2: Optional[float] = Field(default=None, description="Pulse Oximetry Oxygen Saturation (%)")
    known_conditions: Optional[str] = Field(default="None", description="Known comorbidities")
    current_medications: Optional[str] = Field(default="None", description="Current prescribed medications")


class CleanedIntake(BaseModel):
    age: int
    sex: str
    is_pediatric: bool
    chief_complaint: str
    bp_systolic: Optional[float] = None
    bp_diastolic: Optional[float] = None
    heart_rate: Optional[float] = None
    respiratory_rate: Optional[float] = None
    temperature: Optional[float] = None
    spo2: Optional[float] = None


class TriageResponse(BaseModel):
    patient_id: str
    triage_level: int
    triage_level_name: str
    color_code: str
    is_emergency: bool
    recommended_department: str
    rule_override: bool
    rule_applied: Optional[str] = None
    is_abstain: bool
    abstain_reason: Optional[str] = None
    red_flags: List[str] = []
    clinical_why: List[str] = []
    nurse_alerts: List[str] = []
    data_warnings: List[str] = []
    probabilities: Dict[str, float] = {}
    expected_costs: Dict[str, float] = {}
    latency_ms: float
    disclaimer: str
    cleaned_intake: CleanedIntake


class RuleDefinition(BaseModel):
    id: str
    category: str
    condition: str
    urgency_level: str
    action: str
    rationale: str


class RulesResponse(BaseModel):
    total_rules: int
    rules: List[RuleDefinition]
    disclaimer: str
