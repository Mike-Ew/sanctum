@echo off
echo Prayer Slides Generator Setup
echo ================================

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run the app
echo Starting Prayer Slides Generator...
echo Opening browser at http://localhost:8501
streamlit run app.py