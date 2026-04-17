@echo off
REM ==================== STARTUP SCRIPT ====================
REM This script starts the API server and opens the frontend
REM =====================================================

cls
echo.
echo ==================== Autonomous Support Agent ====================
echo Starting API Server and Frontend...
echo ================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install flask flask-cors
)

REM Start the API server in a new window
echo Starting API Server on http://localhost:5000...
start cmd /k python api_server.py

REM Wait for server to start
timeout /t 3 /nobreak

REM Open frontend in default browser
echo Opening Frontend...
start http://localhost:5000/frontend/index.html

echo.
echo ================================================================
echo ✓ Frontend: http://localhost:5000/frontend/index.html
echo ✓ API Docs: http://localhost:5000/api/
echo ✓ Health Check: http://localhost:5000/api/health
echo.
echo Press Ctrl+C in the API server window to stop
echo ================================================================
echo.

pause
