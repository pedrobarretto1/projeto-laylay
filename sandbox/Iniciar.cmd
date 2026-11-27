@echo off
cd /d "%~dp0.."
if exist ".venv314\Scripts\python.exe" (
    ".venv314\Scripts\python.exe" -m sandbox --laylay
) else (
    python -m sandbox --laylay
)
if errorlevel 1 pause
