@echo off
title CrowdPulse Control-Room Frontend Console
echo ======================================================================
echo   Starting CrowdPulse Next.js Operations Console on http://localhost:3000
echo   Connecting to API at http://localhost:8000
echo ======================================================================

cd /d "%~dp0frontend"
if exist .next\BUILD_ID (
  npm run start
) else (
  npm run dev
)
pause
