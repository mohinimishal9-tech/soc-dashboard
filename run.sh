#!/usr/bin/env bash
# One-command setup + launch for the AWS SOC Dashboard (Linux/Mac)
set -e

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example (edit it to add real AWS credentials; demo mode works without them)."
fi

export FLASK_APP=app/app.py
echo ""
echo "=============================================="
echo " AWS SOC Dashboard starting at http://localhost:5000"
echo " (No valid AWS credentials? No problem - it runs in DEMO DATA mode automatically.)"
echo "=============================================="
echo ""

python -m app.app
