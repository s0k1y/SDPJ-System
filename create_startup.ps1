$projectRoot = "E:\Sky毕业设计\4.系统源代码\SDPJ-System"
$scriptContent = @"
# SDPJ-System Start Script
`$ErrorActionPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
`$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SDPJ-System Start Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if database is initialized
`$dbPath = "`$projectRoot\data\db\sdpj.db"
if (-not (Test-Path `$dbPath)) {
    Write-Host "[Init] Database not found, initializing..." -ForegroundColor Yellow
    Push-Location `$projectRoot
    & "C:\Users\asus\.conda\envs\SDPJ-System\python.exe" -m sdpj.infrastructure.utils.scripts.seed_data
    Pop-Location
    Write-Host "[Init] Database initialized" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[Init] Database exists, skipping" -ForegroundColor Green
    Write-Host ""
}

Write-Host "[1/3] Stopping processes on ports 8000 and 5173..." -ForegroundColor Yellow

`$killed = @()
foreach (`$port in @(8000, 5173)) {
    try {
        `$pids = (netstat -ano 2>`$null).Split("`n") | Where-Object { `$_ -match ":`$port\s.*LISTENING" } | ForEach-Object { (`$_ -split '\s+')[-1] } | Where-Object { `$_ -match '^\d+$' }
        foreach (`$procId in `$pids) {
            `$procIdInt = [int]`$procId
            if (`$procIdInt -gt 0 -and `$procIdInt -notin `$killed) {
                Write-Host "  Stopping port `$port process (PID: `$procIdInt)" -ForegroundColor Gray
                Stop-Process -Id `$procIdInt -Force -ErrorAction SilentlyContinue
                `$killed += `$procIdInt
            }
        }
    } catch {}
}

Start-Sleep -Seconds 3
Write-Host "[1/3] Processes stopped" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] Starting backend service..." -ForegroundColor Yellow

`$backendScript = "`$env:TEMP\sdpj_backend.bat"
`$backendContent = "@echo off`r`ncd /d `"`$projectRoot`"`r`nstart /b C:\Users\asus\.conda\envs\SDPJ-System\python.exe -m uvicorn sdpj.ui.webui.backend.app:app --host 0.0.0.0 --port 8000`r`nexit"
`$gbk = [System.Text.Encoding]::GetEncoding(936)
[System.IO.File]::WriteAllText(`$backendScript, `$backendContent, `$gbk)
Start-Process -FilePath `$backendScript -WindowStyle Normal
Start-Sleep -Seconds 5
Write-Host "[2/3] Backend service started" -ForegroundColor Green
Write-Host ""

Write-Host "[3/3] Starting frontend service..." -ForegroundColor Yellow

`$frontendScript = "`$env:TEMP\sdpj_frontend.bat"
`$frontendContent = "@echo off`r`ncd /d `"`$projectRoot`"`r`ncd sdpj\ui\webui\frontend`r`nstart /b npm run dev`r`nexit"
[System.IO.File]::WriteAllText(`$frontendScript, `$frontendContent, `$gbk)
Start-Process -FilePath `$frontendScript -WindowStyle Normal

Start-Sleep -Seconds 5
Write-Host "[3/3] Frontend service started" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Startup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Frontend:     http://localhost:5173" -ForegroundColor Cyan
Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  - If frontend cannot connect to backend, check backend window for errors" -ForegroundColor Yellow
Write-Host "  - Frontend hot-reloads on code changes" -ForegroundColor Yellow
Write-Host "  - Backend requires manual restart on code changes" -ForegroundColor Yellow
Write-Host ""
"@

$utf8Bom = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::WriteAllText("E:\Sky毕业设计\4.系统源代码\SDPJ-System\start.ps1", $scriptContent, $utf8Bom)
Write-Host "Script written with UTF8 BOM"