@echo off
title NOON BOT
cd /d "%~dp0"

openfiles >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Requesting Administrator Privileges...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd.exe -ArgumentList '/k cd /d \"%~dp0\" && python noon_signup_hybrid.py' -Verb RunAs"
    exit /b
)

echo Starting Noon Automation Bot...
python noon_signup_hybrid.py
pause
