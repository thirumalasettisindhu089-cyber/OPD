@echo off
echo ==============================================================================
echo  SMARTTRIAGE AI - OPD Decision Support System (Talent AP 2026 Problem H1)
echo ==============================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.10+
    pause
    exit /b 1
)

:: Ensure synthetic data exists
if not exist "data\dataset.csv" (
    echo [*] Generating synthetic triage dataset and arrival log...
    python generate_synthetic_data.py --samples 5000 --arrivals 800
)

:: Ensure model bundle exists
if not exist "models\model_bundle.joblib" (
    echo [*] Training calibrated ML model and evaluating 4-stage ablations...
    python -m backend.train
)

echo.
echo [*] Running test verification suite...
python -m unittest discover tests
if %errorlevel% neq 0 (
    echo [WARNING] Some tests failed. Please review output above.
)

echo.
echo ==============================================================================
echo  Starting FastAPI Server at http://127.0.0.1:8000
echo  Press Ctrl+C to stop the server
echo ==============================================================================
echo.

uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
