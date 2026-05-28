# SDPJ-System 一键安装脚本 (Windows)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SDPJ-System 一键安装" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot

# --- 检查 Python ---
Write-Host "[1/4] 检查 Python 环境..." -ForegroundColor Yellow

$pythonExe = $null
$pythonCmd = $null

# 优先检查 conda 环境
try {
    $condaInfo = conda info --envs 2>$null | Select-String "SDPJ-System"
    if ($condaInfo) {
        Write-Host "  发现 conda 环境 SDPJ-System，正在激活..." -ForegroundColor Gray
        conda activate SDPJ-System 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonExe = "python"
            $pythonCmd = "python"
        }
    }
} catch {}

# 如果 conda 不可用，检查系统 Python
if (-not $pythonExe) {
    $pythonCmd = "python"
    try {
        $version = & python --version 2>&1
        if ($version -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
                Write-Host "  [错误] Python 版本过低: $version，需要 3.11+" -ForegroundColor Red
                Write-Host "  请安装 Python 3.11+ 或使用 conda 创建环境:" -ForegroundColor Yellow
                Write-Host "    conda create -n SDPJ-System python=3.11" -ForegroundColor Cyan
                Write-Host "    conda activate SDPJ-System" -ForegroundColor Cyan
                exit 1
            }
            $pythonExe = "python"
            Write-Host "  [OK] Python $version" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [错误] 未找到 Python，请先安装 Python 3.11+" -ForegroundColor Red
        Write-Host "  下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}

if (-not $pythonExe) {
    Write-Host "  [错误] 未找到可用的 Python 环境" -ForegroundColor Red
    exit 1
}

# --- 安装 Python 依赖 ---
Write-Host ""
Write-Host "[2/4] 安装 Python 依赖..." -ForegroundColor Yellow

& $pythonCmd -m pip install --upgrade pip -q
& $pythonCmd -m pip install -r requirements.txt -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "  [错误] Python 依赖安装失败" -ForegroundColor Red
    exit 1
}
Write-Host "  [OK] Python 依赖安装完成" -ForegroundColor Green

# --- 检查并安装 Node.js 依赖 ---
Write-Host ""
Write-Host "[3/4] 安装前端依赖..." -ForegroundColor Yellow

$frontendDir = Join-Path $scriptRoot "sdpj\ui\webui\frontend"

try {
    $nodeVersion = & node --version 2>&1
    Write-Host "  [OK] Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [信息] 未找到 Node.js，正在自动安装..." -ForegroundColor Yellow
    
    $installed = $false
    
    # 尝试使用 winget 安装
    try {
        $wingetVersion = & winget --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  正在通过 winget 安装 Node.js 18..." -ForegroundColor Gray
            & winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
            if ($LASTEXITCODE -eq 0) {
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                $installed = $true
            }
        }
    } catch {}
    
    # 尝试使用 Chocolatey 安装
    if (-not $installed) {
        try {
            $chocoVersion = & choco --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  正在通过 Chocolatey 安装 Node.js LTS..." -ForegroundColor Gray
                & choco install nodejs-lts -y
                if ($LASTEXITCODE -eq 0) {
                    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                    $installed = $true
                }
            }
        } catch {}
    }
    
    if (-not $installed) {
        Write-Host "  [错误] 无法自动安装 Node.js" -ForegroundColor Red
        Write-Host "  请手动安装 Node.js 18+: https://nodejs.org/" -ForegroundColor Yellow
        exit 1
    }
    
    try {
        $nodeVersion = & node --version 2>&1
        Write-Host "  [OK] Node.js 安装完成" -ForegroundColor Green
    } catch {
        Write-Host "  [错误] Node.js 安装失败，请手动安装: https://nodejs.org/" -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path "$frontendDir\node_modules")) {
    Write-Host "  正在安装前端依赖 (首次安装可能需要几分钟)..." -ForegroundColor Gray
    Push-Location $frontendDir
    & npm install --silent
    Pop-Location
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [错误] 前端依赖安装失败" -ForegroundColor Red
        exit 1
    }
}
Write-Host "  [OK] 前端依赖安装完成" -ForegroundColor Green

# --- 初始化配置 ---
Write-Host ""
Write-Host "[4/4] 初始化配置..." -ForegroundColor Yellow

# 复制 .env 文件
$envFile = Join-Path $scriptRoot ".env"
$envExample = Join-Path $scriptRoot ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile -Force
    Write-Host "  [OK] 已创建 .env 配置文件" -ForegroundColor Green
}

# 初始化数据库
$dbPath = Join-Path $scriptRoot "sdpj\infrastructure\database\sdpj.db"
if (-not (Test-Path $dbPath)) {
    Write-Host "  正在初始化数据库..." -ForegroundColor Gray
    & $pythonCmd -m sdpj.infrastructure.utils.scripts.seed_data
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] 数据库初始化完成" -ForegroundColor Green
    } else {
        Write-Host "  [警告] 数据库初始化失败，首次启动时会自动初始化" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [OK] 数据库已存在" -ForegroundColor Green
}

# --- 安装完成 ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  安装完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "启动方式:" -ForegroundColor Cyan
Write-Host ""
Write-Host "  WebUI 模式 (图形界面):" -ForegroundColor White
Write-Host "    .\start.ps1" -ForegroundColor Cyan
Write-Host ""
Write-Host "  CLI 模式 (命令行):" -ForegroundColor White
Write-Host "    sdpj --help" -ForegroundColor Cyan
Write-Host ""
