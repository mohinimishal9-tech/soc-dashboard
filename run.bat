@echo off
REM One-command setup + launch for the AWS SOC Dashboard (Windows)

cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if not exist .env (
    copy .env.example .env
    echo Created .env from .env.example (edit it to add real AWS credentials; demo mode works without them).
)

echo.
echo ==============================================
echo  AWS SOC Dashboard starting at http://localhost:5000
echo  (No valid AWS credentials? No problem - it runs in DEMO DATA mode automatically.)
echo ==============================================
echo.

python -m app.app
