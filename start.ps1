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

if ($env:PYTHON_PATH) { $pythonExe = $env:PYTHON_PATH } else { $pythonExe = "python" }
if ($env:API_PORT) { $backendPort = [int]$env:API_PORT } else { $backendPort = 8000 }
$frontendPort = 5173

$sdpjCmd = Get-Command sdpj -ErrorAction SilentlyContinue
if (-not $sdpjCmd) {
    Write-Host "[Init] WARNING: 'sdpj' CLI not found in PATH" -ForegroundColor Yellow
    Write-Host "  Run .\install.ps1 first to register the CLI command" -ForegroundColor Gray
    Write-Host "  Falling back to 'python -m sdpj'" -ForegroundColor Gray
}

# --- Init SSL Certificates (via SecureCommManager) ---
Write-Host "[Init] Ensuring SSL certificates via SecureCommManager..." -ForegroundColor Yellow
$certInfo = & $pythonExe -c "from sdpj.core.secure_comm_manager import SecureCommManager; m = SecureCommManager(); cert, key = m.ensure_certificates(); print(f'{cert}|{key}')"
if ($LASTEXITCODE -eq 0 -and $certInfo) {
    $parts = $certInfo -split '\|'
    $certPath = $parts[0]
    $keyPath = $parts[1]
    Write-Host "[Init] SSL certificates ready" -ForegroundColor Green
} else {
    Write-Host "[Init] WARNING: Failed to get certificate paths, falling back to certs/" -ForegroundColor Red
    $certDir = Join-Path $scriptRoot "certs"
    $certPath = Join-Path $certDir "cert.pem"
    $keyPath = Join-Path $certDir "key.pem"
}
Write-Host ""

# --- Init Database ---
$dbPath = "sdpj\infrastructure\database\sdpj.db"
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
                    $verifyCount = 0
                    while ($verifyCount -lt 10) {
                        $stillAlive = Get-Process -Id $procIdInt -ErrorAction SilentlyContinue
                        if (-not $stillAlive) { break }
                        Start-Sleep -Milliseconds 500
                        $verifyCount++
                    }
                    if ($stillAlive) {
                        Write-Host "  Force killing stubborn process PID $procIdInt via taskkill" -ForegroundColor DarkYellow
                        & taskkill /F /PID $procIdInt 2>$null
                    }
                } else {
                    Write-Host "  Port $Port held by zombie PID $procIdInt, attempting force cleanup" -ForegroundColor DarkGray
                    & taskkill /F /PID $procIdInt 2>$null
                }
            }
        }
    } catch {}
    return $killed.Count
}

Stop-PortProcess -Port $backendPort
Stop-PortProcess -Port $frontendPort

# Force cleanup all Python processes on target ports
Write-Host "  Force cleaning any remaining Python processes..." -ForegroundColor Gray
& taskkill /F /IM python.exe 2>$null | Out-Null
Start-Sleep -Seconds 2

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
    Write-Host "  The port may be locked by another process. Trying alternative port..." -ForegroundColor Yellow
    $backendPort = 8001
}

Write-Host "[1/3] Port cleanup done (waited ${waited}s)" -ForegroundColor Green
Write-Host ""

# --- Step 2: Start backend ---
Write-Host "[2/3] Starting backend service on port $backendPort..." -ForegroundColor Yellow

# SSL certificates are managed by SecureCommManager internally.
# Use "python -m sdpj.ui.webui.backend.app" (not "python -m uvicorn") so SSL kwargs are auto-injected.
$backendArgs = "/k cd /d `"$scriptRoot`" && $pythonExe -m sdpj.ui.webui.backend.app"
Start-Process cmd.exe -ArgumentList $backendArgs -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "[2/3] Backend service started" -ForegroundColor Green
Write-Host ""

# --- Step 3: Start frontend ---
Write-Host "[3/3] Starting frontend service..." -ForegroundColor Yellow

$frontendDir = Join-Path $scriptRoot "sdpj\ui\webui\frontend"

# Sync backend port to frontend via .env.local
$envLocalPath = Join-Path $frontendDir ".env.local"
$envLocalContent = "VITE_BACKEND_PORT=$backendPort"
Set-Content -Path $envLocalPath -Value $envLocalContent -Force -Encoding UTF8
Write-Host "  Synced backend port $backendPort to .env.local" -ForegroundColor Gray

Start-Process cmd.exe -ArgumentList "/k cd /d `"$frontendDir`" && npm run dev" -WindowStyle Normal

Start-Sleep -Seconds 3
Write-Host "[3/3] Frontend service started" -ForegroundColor Green
Write-Host ""

# --- Summary ---
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Startup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend API:  https://localhost:$backendPort" -ForegroundColor Cyan
Write-Host "  Frontend:     https://localhost:$frontendPort" -ForegroundColor Cyan
Write-Host "  API Docs:     https://localhost:$backendPort/docs" -ForegroundColor Cyan
Write-Host ""

Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  - If frontend cannot connect to backend, check the backend window for errors" -ForegroundColor Yellow
Write-Host "  - Frontend hot-reloads on code changes" -ForegroundColor Yellow
Write-Host "  - Backend requires manual restart on code changes" -ForegroundColor Yellow
Write-Host ""
