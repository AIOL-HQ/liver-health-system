@echo off
title Liver Health Smart System Launcher
cd /d "%~dp0"

echo ==========================================
echo   Liver Health Smart System - Auto Setup
echo ==========================================

if not exist venv (
    echo [1/4] Creating virtual environment...
    py -m venv venv 2>nul
    if errorlevel 1 python -m venv venv
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing/updating required libraries...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Starting the project...
start http://127.0.0.1:5000
python app.py

pause
