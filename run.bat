@echo off
echo ============================================================
echo Starting CarbonLens - Digital Carbon Footprint Analytics
echo ============================================================

IF NOT EXIST .venv (
    echo Creating virtual environment .venv...
    python -m venv .venv
    IF ERRORLEVEL 1 (
        echo [ERROR] Failed to create virtual environment. Ensure Python 3.11+ is installed.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

echo Checking and installing requirements...
pip install -r requirements.txt

echo Starting CarbonLens Web Application...
python app.py
pause
