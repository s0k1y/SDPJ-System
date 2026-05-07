# SDPJ-System Start Script
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SDPJ-System Start Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

$pythonExe = "C:\Users\asus\.conda\envs\SDPJ-System\python.exe"
$backendPort = 8000
$frontendPort = 5173

# --- Init Database ---
$dbPath = "data\db\sdpj.db"
if (-not (Test-Path $dbPath)) {
    Write-Host "[Init] Database not found, initializing..." -ForegroundColor Yellow
    & $pythonExe -m sdpj.infrastructure.utils.scripts.seed_data
    Write-Host "[Init] Database initialized" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[Init] Database exists, skipping" -ForegroundColor Green
    Write-Host ""
}

# --- Step 1: Kill processes on target ports ---
Write-Host "[1/3] Stopping processes on ports $backendPort and $frontendPort..." -ForegroundColor Yellow

function Stop-PortProcess {
    param([int]$Port)
    $killed = @()
    try {
        $pids = (netstat -ano 2>$null).Split("`n") |
            Where-Object { $_ -match ":$Port\s.*LISTENING" } |
            ForEach-Object { ($_ -split '\s+')[-1] } |
            Where-Object { $_ -match '^\d+$' }

        foreach ($procId in $pids) {
            $procIdInt = [int]$procId
            if ($procIdInt -gt 0 -and $procIdInt -notin $killed) {
                $proc = Get-Process -Id $procIdInt -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "  Stopping port $Port process (PID: $procIdInt - $($proc.ProcessName))" -ForegroundColor Gray
                    Stop-Process -Id $procIdInt -Force -ErrorAction SilentlyContinue
                    $killed += $procIdInt
                } else {
                    Write-Host "  Port $Port held by zombie PID $procIdInt (process already dead, waiting for OS to release)" -ForegroundColor DarkGray
                }
            }
        }
    } catch {}
    return $killed.Count
}

Stop-PortProcess -Port $backendPort
Stop-PortProcess -Port $frontendPort

# Wait for OS to release ports (including zombie holds)
$maxWait = 15
$waited = 0
while ($waited -lt $maxWait) {
    $stillHeld = (netstat -ano 2>$null).Split("`n") |
        Where-Object { $_ -match ":$backendPort\s.*LISTENING" }
    if (-not $stillHeld) { break }
    Start-Sleep -Seconds 1
    $waited++
}

if ($waited -ge $maxWait) {
    Write-Host "[1/3] WARNING: Port $backendPort still occupied after ${maxWait}s wait" -ForegroundColor Red
    Write-Host "  The port may be in a zombie state. Trying alternative port..." -ForegroundColor Yellow
    $backendPort = 8001
}

Write-Host "[1/3] Port cleanup done (waited ${waited}s)" -ForegroundColor Green
Write-Host ""

# --- Step 2: Start backend ---
Write-Host "[2/3] Starting backend service on port $backendPort..." -ForegroundColor Yellow

# Use cmd /k so the window stays open on error (prevents flash-close)
$backendArgs = "/k cd /d `"$scriptRoot`" && $pythonExe -m uvicorn sdpj.ui.webui.backend.app:app --host 0.0.0.0 --port $backendPort"
Start-Process cmd.exe -ArgumentList $backendArgs -WindowStyle Normal

# Wait and verify backend is actually running
$backendReady = $false
for ($i = 0; $i -lt 10; $i++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$backendPort/docs" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {}
}

if ($backendReady) {
    Write-Host "[2/3] Backend service started successfully" -ForegroundColor Green
} else {
    Write-Host "[2/3] WARNING: Backend may not be running - check the backend window for errors" -ForegroundColor Red
}
Write-Host ""

# --- Step 3: Start frontend ---
Write-Host "[3/3] Starting frontend service..." -ForegroundColor Yellow

$frontendDir = Join-Path $scriptRoot "sdpj\ui\webui\frontend"
Start-Process cmd.exe -ArgumentList "/k cd /d `"$frontendDir`" && npm run dev" -WindowStyle Normal

Start-Sleep -Seconds 3
Write-Host "[3/3] Frontend service started" -ForegroundColor Green
Write-Host ""

# --- Summary ---
Write-Host "========================================" -ForegroundColor $(if ($backendReady) {"Green"} else {"Yellow"})
Write-Host "  Startup Complete!" -ForegroundColor $(if ($backendReady) {"Green"} else {"Yellow"})
Write-Host "========================================" -ForegroundColor $(if ($backendReady) {"Green"} else {"Yellow"})
Write-Host ""
Write-Host "  Backend API:  http://localhost:$backendPort" -ForegroundColor Cyan
Write-Host "  Frontend:     http://localhost:$frontendPort" -ForegroundColor Cyan
Write-Host "  API Docs:     http://localhost:$backendPort/docs" -ForegroundColor Cyan
Write-Host ""

if ($backendPort -ne 8000) {
    Write-Host "  NOTE: Backend is running on alternate port $backendPort (port 8000 was occupied)" -ForegroundColor Yellow
    Write-Host "  You may need to update the frontend proxy config to match" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  - If frontend cannot connect to backend, check the backend window for errors" -ForegroundColor Yellow
Write-Host "  - Frontend hot-reloads on code changes" -ForegroundColor Yellow
Write-Host "  - Backend requires manual restart on code changes" -ForegroundColor Yellow
Write-Host ""
