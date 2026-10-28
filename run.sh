#!/usr/bin/env bash
# SmartTriage AI - One-Command Setup & Launch (Linux / macOS)
set -e

echo "=============================================================================="
echo " SMARTTRIAGE AI - OPD Decision Support System (Talent AP 2026 Problem H1)"
echo "=============================================================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 not found. Please install Python 3.10+"
    exit 1
fi

# Ensure synthetic data exists
if [ ! -f "data/dataset.csv" ]; then
    echo "[*] Generating synthetic triage dataset and arrival log..."
    python3 generate_synthetic_data.py --samples 5000 --arrivals 800
fi

# Ensure model exists
if [ ! -f "models/model_bundle.joblib" ]; then
    echo "[*] Training calibrated ML model and evaluating 4-stage ablations..."
    python3 -m backend.train
fi

echo "[*] Running test verification suite..."
python3 -m unittest discover tests

echo "=============================================================================="
echo " Starting FastAPI Server at http://127.0.0.1:8000"
echo "=============================================================================="
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
