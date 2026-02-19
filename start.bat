@echo off
echo ====================================
echo   Researcho - Starting Backend
echo ====================================

:: Check if venv exists, create if not
if not exist "backend\venv" (
    echo Creating virtual environment...
    python -m venv backend\venv
)

:: Activate venv
call backend\venv\Scripts\activate.bat

:: Install dependencies (only if needed)
echo Installing/checking dependencies...
pip install -r backend\requirements.txt --quiet

:: Copy .env.example to backend\.env if it doesn't exist yet
if not exist "backend\.env" (
    if exist ".env.example" (
        copy .env.example backend\.env >nul
        echo Created backend\.env from .env.example
    )
)

:: Start the server FROM PROJECT ROOT using --app-dir
:: This ensures backend\config.py resolves .env correctly via __file__ path
echo.
echo Starting Researcho backend on http://localhost:8000
echo Visit http://localhost:8000 for the UI
echo Visit http://localhost:8000/docs for the API docs
echo Press Ctrl+C to stop.
echo.

backend\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir backend
