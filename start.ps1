$ErrorActionPreference = "SilentlyContinue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SDPJ-System 启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查数据库是否已初始化
$dbPath = "E:\Sky毕业设计\4.系统源代码\SDPJ-System\data\db\sdpj.db"
if (-not (Test-Path $dbPath)) {
    Write-Host "[初始化] 数据库不存在，正在初始化..." -ForegroundColor Yellow
    & "C:\Users\asus\.conda\envs\SDPJ-System\python.exe" -m sdpj.infrastructure.utils.scripts.seed_data
    Write-Host "[初始化] 数据库初始化完成" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[初始化] 数据库已存在，跳过初始化" -ForegroundColor Green
    Write-Host ""
}

Write-Host "[1/3] 正在停止占用端口 8000 和 5173 的进程..." -ForegroundColor Yellow

$killed = @()
foreach ($port in @(8000, 5173)) {
    try {
        $pids = (netstat -ano 2>$null).Split("`n") | Where-Object { $_ -match ":$port\s.*LISTENING" } | ForEach-Object { ($_ -split '\s+')[-1] } | Where-Object { $_ -match '^\d+$' }
        foreach ($pid in $pids) {
            $pidInt = [int]$pid
            if ($pidInt -gt 0 -and $pidInt -notin $killed) {
                Write-Host "  停止端口 $port 占用进程 (PID: $pidInt)" -ForegroundColor Gray
                Stop-Process -Id $pidInt -Force -ErrorAction SilentlyContinue
                $killed += $pidInt
            }
        }
    } catch {}
}

Start-Sleep -Seconds 3
Write-Host "[1/3] 进程已停止" -ForegroundColor Green
Write-Host ""

Write-Host "[2/3] 正在启动后端服务..." -ForegroundColor Yellow

$batDir = "$env:TEMP\sdpj"
if (-not (Test-Path $batDir)) { New-Item -ItemType Directory -Path $batDir -Force | Out-Null }

# 使用 UTF-8 编码写入 bat 文件，避免中文路径乱码
$backendContent = "@echo off`r`ncd /d `"E:\Sky毕业设计\4.系统源代码\SDPJ-System`"`r`nif %ERRORLEVEL% NEQ 0 (`r`n    echo [ERROR] Cannot cd to project dir`r`n    exit /b 1`r`n)`r`necho [Backend] Starting FastAPI server...`r`nC:\Users\asus\.conda\envs\SDPJ-System\python.exe -m uvicorn sdpj.ui.webui.backend.app:app --host 0.0.0.0 --port 8000"
$gbk = [System.Text.Encoding]::GetEncoding(936)
[System.IO.File]::WriteAllText("$batDir\start_backend.bat", $backendContent, $gbk)

Start-Process "$batDir\start_backend.bat"
Start-Sleep -Seconds 5
Write-Host "[2/3] 后端服务已启动" -ForegroundColor Green
Write-Host ""

Write-Host "[3/3] 正在启动前端服务..." -ForegroundColor Yellow

# 使用 UTF-8 编码写入 bat 文件，避免中文路径乱码
$frontendContent = "@echo off`r`ncd /d `"E:\Sky毕业设计\4.系统源代码\SDPJ-System\sdpj\ui\webui\frontend`"`r`nif %ERRORLEVEL% NEQ 0 (`r`n    echo [ERROR] Cannot cd to frontend dir`r`n    exit /b 1`r`n)`r`necho [Frontend] Starting Vite dev server...`r`nnpm run dev"
$gbk = [System.Text.Encoding]::GetEncoding(936)
[System.IO.File]::WriteAllText("$batDir\start_frontend.bat", $frontendContent, $gbk)

Start-Process "$batDir\start_frontend.bat"
Start-Sleep -Seconds 3
Write-Host "[3/3] 前端服务已启动" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  后端 API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  前端界面:  http://localhost:5173" -ForegroundColor Cyan
Write-Host "  API 文档:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示：" -ForegroundColor Yellow
Write-Host "  - 如果前端连接不上后端，请检查后端窗口是否有错误" -ForegroundColor Yellow
Write-Host "  - 修改前端代码后会自动热重载，无需重启" -ForegroundColor Yellow
Write-Host "  - 修改后端代码后需要手动重启后端服务" -ForegroundColor Yellow
Write-Host ""
