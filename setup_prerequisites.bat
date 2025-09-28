@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Prerequisites Setup Script
echo ========================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script should be run as administrator for best results
    echo Some installations may require elevated privileges
    echo.
)

:: Check if Chocolatey is installed
echo Checking for Chocolatey package manager...
choco --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Chocolatey not found. Installing Chocolatey...
    echo.
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    if %errorlevel% neq 0 (
        echo Warning: Failed to install Chocolatey
        echo You may need to install dependencies manually
    ) else (
        echo ✓ Chocolatey installed successfully
    )
) else (
    echo ✓ Chocolatey is already installed
)

:: Check if winget is available
echo.
echo Checking for winget...
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo winget not available. This is included in Windows 10/11 App Installer
    echo Please update Windows or install App Installer from Microsoft Store
) else (
    echo ✓ winget is available
)

:: Install Python if not present
echo.
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Installing Python 3.11...
    if exist "C:\ProgramData\chocolatey\bin\choco.exe" (
        choco install python311 -y
    ) else (
        winget install Python.Python.3.11
    )
    if %errorlevel% neq 0 (
        echo Error: Failed to install Python
        echo Please install Python manually from https://python.org
        pause
        exit /b 1
    ) else (
        echo ✓ Python installed successfully
        echo Please restart your command prompt to use Python
    )
) else (
    echo ✓ Python is already installed
)

:: Install Git if not present
echo.
echo Checking Git installation...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Git not found. Installing Git...
    if exist "C:\ProgramData\chocolatey\bin\choco.exe" (
        choco install git -y
    ) else (
        winget install Git.Git
    )
    if %errorlevel% neq 0 (
        echo Error: Failed to install Git
        echo Please install Git manually from https://git-scm.com
    ) else (
        echo ✓ Git installed successfully
    )
) else (
    echo ✓ Git is already installed
)

:: Install Docker Desktop if not present
echo.
echo Checking Docker Desktop installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker Desktop not found. Installing Docker Desktop...
    if exist "C:\ProgramData\chocolatey\bin\choco.exe" (
        choco install docker-desktop -y
    ) else (
        winget install Docker.DockerDesktop
    )
    if %errorlevel% neq 0 (
        echo Error: Failed to install Docker Desktop
        echo Please install Docker Desktop manually from https://www.docker.com/products/docker-desktop/
        echo After installation, start Docker Desktop and run the main script
    ) else (
        echo ✓ Docker Desktop installed successfully
        echo Please start Docker Desktop and run the main script
    )
) else (
    echo ✓ Docker Desktop is already installed
)

:: Install curl if not present (for health checks)
echo.
echo Checking curl installation...
curl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo curl not found. Installing curl...
    if exist "C:\ProgramData\chocolatey\bin\choco.exe" (
        choco install curl -y
    ) else (
        winget install curl.curl
    )
    if %errorlevel% neq 0 (
        echo Warning: Failed to install curl
        echo Health checks may not work properly
    ) else (
        echo ✓ curl installed successfully
    )
) else (
    echo ✓ curl is already installed
)

echo.
echo ========================================
echo    Prerequisites Setup Complete
echo ========================================
echo.
echo Next steps:
echo 1. Restart your command prompt if Python was installed
echo 2. Start Docker Desktop if it was installed
echo 3. Run run_docker_app.bat to start the application
echo.
pause
