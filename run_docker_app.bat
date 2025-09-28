@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Xeni Hotelier Integration Docker
echo ========================================
echo.

:: Set the ports used by the application
set APP_PORT=8000
set MYSQL_PORT=3307

:: Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Not running as administrator. Some operations may require elevated privileges.
    echo If you encounter permission issues, please run this script as administrator.
    echo.
)

:: Check prerequisites
echo Checking prerequisites...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11 or later from https://python.org
    pause
    exit /b 1
)
echo ✓ Python is installed

:: Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)
echo ✓ pip is available

:: Check if Git is installed (for Docker build context)
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Git is not installed. This may affect Docker build context.
    echo Please install Git from https://git-scm.com
    echo.
) else (
    echo ✓ Git is installed
)

:: Check if .env file exists, create if not
if not exist ".env" (
    echo Creating .env file from template...
    if exist "env.example" (
        copy "env.example" ".env" >nul
        echo ✓ Created .env file from env.example
        echo Please edit .env file to add your XENI_API_KEY
    ) else (
        echo Warning: env.example not found. Creating basic .env file...
        echo # Xeni API Configuration > .env
        echo XENI_API_KEY=your_xeni_api_key_here >> .env
        echo # API Configuration File >> .env
        echo API_CONFIG_FILE=api_config.json >> .env
        echo # Application Configuration >> .env
        echo PYTHONPATH=/app >> .env
        echo ✓ Created basic .env file
        echo Please edit .env file to add your XENI_API_KEY
    )
    echo.
) else (
    echo ✓ .env file exists
)

:: Check if config files exist
if not exist "app\config\api_config.json" (
    echo Error: api_config.json not found in app\config\
    echo Please ensure the configuration file exists
    pause
    exit /b 1
)
echo ✓ Configuration files exist

:: Check if requirements.txt exists
if not exist "requirements.txt" (
    echo Error: requirements.txt not found
    echo Please ensure requirements.txt exists
    pause
    exit /b 1
)
echo ✓ requirements.txt exists

:: Function to check if port is in use
:check_port
set port=%1
echo Checking if port %port% is available...
netstat -ano | findstr ":%port% " >nul
if %errorlevel% equ 0 (
    echo Port %port% is in use. Finding and killing process...
    
    :: Get the PID of the process using the port
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%port% "') do (
        set pid=%%a
        echo Killing process with PID: !pid!
        taskkill /PID !pid! /F >nul 2>&1
        if !errorlevel! equ 0 (
            echo Successfully killed process on port %port%
        ) else (
            echo Warning: Could not kill process on port %port% (may require admin privileges)
        )
    )
    
    :: Wait a moment for the port to be released
    timeout /t 2 /nobreak >nul
    
    :: Check again if port is still in use
    netstat -ano | findstr ":%port% " >nul
    if !errorlevel! equ 0 (
        echo Warning: Port %port% is still in use after attempting to kill process
    ) else (
        echo Port %port% is now available
    )
) else (
    echo Port %port% is available
)

:: Check if Docker is installed and running
echo.
echo Checking Docker installation...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed or not running
    echo.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/
    echo After installation, start Docker Desktop and try again
    echo.
    echo Alternative: Install Docker using Chocolatey:
    echo   choco install docker-desktop
    echo.
    echo Alternative: Install Docker using winget:
    echo   winget install Docker.DockerDesktop
    pause
    exit /b 1
)
echo ✓ Docker is installed and running

:: Check if Docker Compose is available
echo Checking Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Docker Compose standalone not found, trying Docker Compose plugin...
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Docker Compose is not available
        echo Please install Docker Compose or update Docker Desktop
        echo.
        echo Docker Desktop includes Docker Compose, please ensure you have the latest version
        pause
        exit /b 1
    ) else (
        echo ✓ Docker Compose plugin is available
        set USE_COMPOSE_PLUGIN=1
    )
) else (
    echo ✓ Docker Compose standalone is available
    set USE_COMPOSE_PLUGIN=0
)

:: Install Python dependencies locally (for development/testing)
echo.
echo Installing Python dependencies locally...
if exist "requirements.txt" (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo Warning: Some Python dependencies failed to install
        echo This may not affect Docker operation but could impact local development
    ) else (
        echo ✓ Python dependencies installed successfully
    )
) else (
    echo Warning: requirements.txt not found, skipping local dependency installation
)

:: Check ports
echo.
echo Checking application ports...
call :check_port %APP_PORT%
call :check_port %MYSQL_PORT%

:: Stop and remove existing containers
echo.
echo Stopping and removing existing containers...
if %USE_COMPOSE_PLUGIN%==1 (
    docker compose down --remove-orphans
) else (
    docker-compose down --remove-orphans
)
if %errorlevel% neq 0 (
    echo Warning: Some containers may not have stopped cleanly
)

:: Remove any dangling images (optional)
echo.
echo Cleaning up unused Docker resources...
docker system prune -f >nul 2>&1

:: Build and start the application
echo.
echo Building and starting the application...
echo This may take a few minutes on first run...
if %USE_COMPOSE_PLUGIN%==1 (
    docker compose up --build -d
) else (
    docker-compose up --build -d
)

if %errorlevel% neq 0 (
    echo.
    echo Error: Failed to start the application
    if %USE_COMPOSE_PLUGIN%==1 (
        echo Check the logs with: docker compose logs
    ) else (
        echo Check the logs with: docker-compose logs
    )
    pause
    exit /b 1
)

:: Wait for services to be ready
echo.
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul

:: Check if services are running
echo.
echo Checking service status...
if %USE_COMPOSE_PLUGIN%==1 (
    docker compose ps
) else (
    docker-compose ps
)

:: Test the application health endpoint
echo.
echo Testing application health...
timeout /t 5 /nobreak >nul
curl -s http://localhost:%APP_PORT%/health >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    Application Started Successfully!
    echo ========================================
    echo.
    echo Application URL: http://localhost:%APP_PORT%
    echo Health Check: http://localhost:%APP_PORT%/health
    echo API Documentation: http://localhost:%APP_PORT%/docs
    echo.
    echo MySQL Database:
    echo   Host: localhost
    echo   Port: %MYSQL_PORT%
    echo   Database: getmyhotels
    echo   Username: getmyhotels
    echo   Password: getmyhotels123
    echo.
    if %USE_COMPOSE_PLUGIN%==1 (
        echo To view logs: docker compose logs -f
        echo To stop: docker compose down
    ) else (
        echo To view logs: docker-compose logs -f
        echo To stop: docker-compose down
    )
    echo.
) else (
    echo.
    echo Warning: Application may not be fully ready yet
    if %USE_COMPOSE_PLUGIN%==1 (
        echo Check the logs with: docker compose logs
    ) else (
        echo Check the logs with: docker-compose logs
    )
    echo Try accessing: http://localhost:%APP_PORT%/health
    echo.
)

:: Show logs for a few seconds
echo Showing recent logs (press Ctrl+C to stop viewing logs):
timeout /t 3 /nobreak >nul
if %USE_COMPOSE_PLUGIN%==1 (
    docker compose logs --tail=20
) else (
    docker-compose logs --tail=20
)

echo.
echo Press any key to continue...
pause >nul

endlocal
