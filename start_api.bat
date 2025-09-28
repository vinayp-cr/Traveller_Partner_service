@echo off
echo Starting Hotel Integration API Server...
echo ========================================

REM Set environment variables
set PYTHONPATH=D:\project\GetMyHotels\Xeni_Hotelier_Integration\TravelPartnerServices
set API_CONFIG_FILE=api_config.json

REM Check if port 8000 is in use
echo Checking if port 8000 is available...
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo Port 8000 is in use. Finding and killing the process...
    
    REM Find the PID using port 8000
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
        echo Killing process with PID: %%a
        taskkill /PID %%a /F
        if %errorlevel% == 0 (
            echo Successfully killed process on port 8000
        ) else (
            echo Failed to kill process on port 8000
        )
    )
    
    REM Wait a moment for the port to be released
    timeout /t 2 /nobreak >nul
) else (
    echo Port 8000 is available.
)

REM Start the API server
echo Starting API server on port 8000...
uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
