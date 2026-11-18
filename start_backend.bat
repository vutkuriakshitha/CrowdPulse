@echo off
title CrowdPulse FastAPI Backend Server
echo ======================================================================
echo   Starting CrowdPulse Backend API on http://127.0.0.1:8000
echo   API Docs available at http://127.0.0.1:8000/docs
echo ======================================================================

cd /d "%~dp0backend"
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
  uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
) else (
  echo [ERROR] Virtual environment not found in backend\.venv
  echo Please run: python -m venv backend\.venv and pip install -r requirements.txt
)
pause
