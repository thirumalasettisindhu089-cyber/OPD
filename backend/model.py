"""
backend/model.py - Hybrid ML Pipeline, Asymmetric Cost Optimizer & Abstention
SmartTriage AI - Talent AP Mega Hackathon 2026

Features:
- Dual-ngram TF-IDF (word n-grams 1-2 and char n-grams 3-4) on chief complaint
- Bag of terms for comorbidities and current medications
- Standard scaled physiological vitals with explicit binary missing indicators
- Calibrated probabilistic classifier (LinearSVC with Platt scaling + Logistic Regression baseline)
- Asymmetric Expected Cost Minimizer (evaluates expected risk under asymmetric penalty matrix)
- Uncertainty-aware Abstention Mechanism ("CANNOT ASSESS - SEND TO NURSE NOW")
- Multi-class Specialty Department classification
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from scipy.sparse import hstack, csr_matrix

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report

from backend.config import ASYMMETRIC_COST_MATRIX, ABSTENTION_COSTS, CONFIDENCE_THRESHOLD
from backend.data_cleaner import clean_patient_record, clean_text_complaint


class SmartTriagePipeline:
    def __init__(self, confidence_threshold: float = CONFIDENCE_THRESHOLD):
        self.confidence_threshold = confidence_threshold

        # Feature extractors
        self.text_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            analyzer="word",
            max_features=2000,
            sublinear_tf=True
        )
        self.char_vectorizer = TfidfVectorizer(
            ngram_range=(3, 4),
            analyzer="char",
            max_features=1500,
            sublinear_tf=True
        )
        self.cond_vectorizer = TfidfVectorizer(
            ngram_range=(1, 1),
            max_features=250
        )

        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()

        # Classifiers
        # Baseline model: Logistic Regression
        self.baseline_model = LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=42
        )
        # Strong model: Calibrated LinearSVC (Platt Sigmoid Scaling for well-calibrated probabilities)
        base_svc = LinearSVC(C=1.0, dual="auto", max_iter=2500, random_state=42)
        self.strong_model = CalibratedClassifierCV(estimator=base_svc, method="sigmoid", cv=3)

        # Department classifier
        self.dept_model = LogisticRegression(max_iter=1000, random_state=42)

        self.is_fitted = False
        self.active_model_name = "Calibrated LinearSVC"

    def _prepare_feature_matrices(self, df: pd.DataFrame, fit: bool = False) -> csr_matrix:
        """Constructs rich multimodal sparse feature matrix."""
        # 1. Text representations
        complaints = df["chief_complaint"].fillna("").astype(str)
        if fit:
            X_word = self.text_vectorizer.fit_transform(complaints)
            X_char = self.char_vectorizer.fit_transform(complaints)
        else:
            X_word = self.text_vectorizer.transform(complaints)
            X_char = self.char_vectorizer.transform(complaints)

        # 2. Medical conditions and medications
        cond_text = (df["known_conditions"].fillna("") + " " + df["current_medications"].fillna("")).astype(str)
        if fit:
            X_cond = self.cond_vectorizer.fit_transform(cond_text)
        else:
            X_cond = self.cond_vectorizer.transform(cond_text)

        # 3. Numeric vitals with missingness indicators
        vitals_cols = ["age", "bp_systolic", "bp_diastolic", "heart_rate", "respiratory_rate", "temperature", "spo2"]
        raw_num = df[vitals_cols].to_numpy(dtype=float)

        # Missing indicators (1 if missing/nan, 0 otherwise)
        missing_indicators = np.isnan(raw_num).astype(float)

        # Impute and scale numerical vitals
        if fit:
            imputed_num = self.imputer.fit_transform(raw_num)
            scaled_num = self.scaler.fit_transform(imputed_num)
        else:
            imputed_num = self.imputer.transform(raw_num)
            scaled_num = self.scaler.transform(imputed_num)

        X_num = np.hstack([scaled_num, missing_indicators])
        X_num_sparse = csr_matrix(X_num)

        # Combine all modalities
        X_all = hstack([X_word, X_char, X_cond, X_num_sparse]).tocsr()
        return X_all

    def fit(self, df_train: pd.DataFrame):
        """Fits baseline, strong calibrated model, and department classifier."""
        X_train = self._prepare_feature_matrices(df_train, fit=True)
        y_train_level = df_train["triage_level"].to_numpy(dtype=int)
        y_train_dept = df_train["recommended_department"].to_numpy(dtype=str)

        # Fit triage models
        self.baseline_model.fit(X_train, y_train_level)
        self.strong_model.fit(X_train, y_train_level)

        # Fit department model
        self.dept_model.fit(X_train, y_train_dept)

        self.is_fitted = True

    def predict_probabilities(self, X: csr_matrix, use_baseline: bool = False) -> np.ndarray:
        """Returns calibrated probability distribution across Levels 1-5."""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        model = self.baseline_model if use_baseline else self.strong_model
        probs = model.predict_proba(X)
        return probs

    def predict_cost_minimizing_level(self, probs: np.ndarray) -> Tuple[int, np.ndarray]:
        """
        Calculates expected asymmetric cost for each candidate level j:
        E[Cost(j)] = Sum_{i=1..5} P(True = i) * Cost(i, j)
        Picks j* = argmin_j E[Cost(j)].
        """
        # probs has shape (5,) for Levels 1, 2, 3, 4, 5
        # ASYMMETRIC_COST_MATRIX has shape (5, 5) -> row i is true level, col j is predicted level
        # expected_cost_j = probs @ Cost[:, j]
        expected_costs = np.dot(probs, ASYMMETRIC_COST_MATRIX)
        # Optimal level is 1-indexed (argmax of negative cost)
        best_idx = int(np.argmin(expected_costs))
        best_level = best_idx + 1
        return best_level, expected_costs

    def check_abstention(
        self,
        probs: np.ndarray,
        clean_record: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Determines whether to abstain ("CANNOT ASSESS - SEND TO NURSE NOW").
        Triggers when:
        1. Model confidence (max probability) is below calibrated threshold.
        2. Critical vitals are missing/impossible AND complaint text is too short or ambiguous.
        3. High entropy across all classes.
        """
        max_prob = float(np.max(probs))
        flags = clean_record.get("flags", {})
        complaint = clean_record.get("chief_complaint", "")

        # Count missing/impossible vital sign indicators
        vital_missing_count = sum([
            1 for k in ["bp_systolic_missing", "heart_rate_missing", "spo2_missing", "temperature_missing"]
            if flags.get(k, False)
        ])

        # Rule A: Extreme uncertainty across all 5 triage levels
        if max_prob < self.confidence_threshold:
            return True, f"High model uncertainty (Confidence {max_prob*100:.1f}% < {self.confidence_threshold*100:.0f}%)"

        # Rule B: Critical vitals missing AND complaint text is short/vague (< 8 characters)
        if vital_missing_count >= 2 and len(complaint) < 8:
            return True, f"Critical vitals missing ({vital_missing_count} vitals missing) with uninformative complaint text"

        # Rule C: All vitals missing and non-informative text
        if vital_missing_count >= 3:
            return True, "Multiple critical vitals unavailable for safe algorithmic triage"

        return False, None

    def predict_single(
        self,
        raw_record: Dict[str, Any],
        use_cost_minimizer: bool = True,
        use_baseline: bool = False
    ) -> Dict[str, Any]:
        """
        Inference on a single patient intake record.
        Integrates cleaning, probability estimation, department prediction, cost minimization, and abstention.
        """
        # 1. Clean intake
        cleaned = clean_patient_record(raw_record)

        # 2. Convert to single-row dataframe for feature extraction
        df_single = pd.DataFrame([cleaned])
        X_single = self._prepare_feature_matrices(df_single, fit=False)

        # 3. Predict class probabilities
        probs = self.predict_probabilities(X_single, use_baseline=use_baseline)[0]
        # Guarantee 5-element array
        if len(probs) < 5:
            padded_probs = np.zeros(5)
            padded_probs[:len(probs)] = probs
            probs = padded_probs

        # 4. Standard argmax vs Cost-minimizing prediction
        argmax_level = int(np.argmax(probs)) + 1
        cost_min_level, expected_costs = self.predict_cost_minimizing_level(probs)
        selected_level = cost_min_level if use_cost_minimizer else argmax_level

        # 5. Department prediction
        dept_pred = str(self.dept_model.predict(X_single)[0])

        # 6. Check abstention
        should_abstain, abstain_reason = self.check_abstention(probs, cleaned)

        # Class probabilities mapping
        prob_dict = {
            f"Level {lvl}": round(float(probs[lvl-1]), 4)
            for lvl in range(1, 6)
        }
        cost_dict = {
            f"Level {lvl}": round(float(expected_costs[lvl-1]), 2)
            for lvl in range(1, 6)
        }

        return {
            "model_level": selected_level,
            "argmax_level": argmax_level,
            "cost_min_level": cost_min_level,
            "recommended_department": dept_pred,
            "probabilities": prob_dict,
            "expected_costs": cost_dict,
            "confidence": round(float(np.max(probs)), 4),
            "should_abstain": should_abstain,
            "abstain_reason": abstain_reason,
            "cleaned_record": cleaned,
        }

    def save(self, filepath: str):
        """Serializes trained pipeline bundle to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)
        print(f"[+] Model bundle successfully saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "SmartTriagePipeline":
        """Loads serialized pipeline bundle."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found at {filepath}")
        return joblib.load(filepath)
