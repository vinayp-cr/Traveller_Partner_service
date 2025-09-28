# Hotel Integration API Server Startup Script
Write-Host "Starting Hotel Integration API Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Set environment variables
$env:PYTHONPATH = "D:\project\GetMyHotels\Xeni_Hotelier_Integration\TravelPartnerServices"
$env:API_CONFIG_FILE = "api_config.json"

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $connection -ne $null
}

# Function to kill process on port
function Stop-ProcessOnPort {
    param([int]$Port)
    try {
        $processes = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
        foreach ($pid in $processes) {
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Killing process: $($process.ProcessName) (PID: $pid)" -ForegroundColor Yellow
                Stop-Process -Id $pid -Force
                Write-Host "Successfully killed process on port $Port" -ForegroundColor Green
            }
        }
    }
    catch {
        Write-Host "Error killing process on port $Port : $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Check if port 8000 is available
Write-Host "Checking if port 8000 is available..." -ForegroundColor Cyan
if (Test-Port -Port 8000) {
    Write-Host "Port 8000 is in use. Finding and killing the process..." -ForegroundColor Yellow
    Stop-ProcessOnPort -Port 8000
    
    # Wait a moment for the port to be released
    Write-Host "Waiting for port to be released..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    
    # Double check if port is now free
    if (Test-Port -Port 8000) {
        Write-Host "Warning: Port 8000 is still in use after attempting to kill processes" -ForegroundColor Red
    } else {
        Write-Host "Port 8000 is now available" -ForegroundColor Green
    }
} else {
    Write-Host "Port 8000 is available" -ForegroundColor Green
}

# Start the API server
Write-Host "Starting API server on port 8000..." -ForegroundColor Cyan
Write-Host "Server will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health Check: http://localhost:8000/health" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green

try {
    uvicorn app.main:app --host 0.0.0.0 --port 8000
}
catch {
    Write-Host "Error starting the server: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
