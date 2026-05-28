#!/bin/bash

# SDPJ-System 一键安装脚本 (Linux/macOS)
set -e

echo "========================================"
echo "  SDPJ-System 一键安装"
echo "========================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- 检查 Python ---
echo "[1/4] 检查 Python 环境..."

PYTHON_CMD=""

# 优先检查 conda 环境
if command -v conda &> /dev/null; then
    if conda info --envs 2>/dev/null | grep -q "SDPJ-System"; then
        echo "  发现 conda 环境 SDPJ-System，正在激活..."
        eval "$(conda shell.bash hook)"
        conda activate SDPJ-System 2>/dev/null || true
    fi
fi

# 检查 Python
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        version=$("$cmd" --version 2>&1 | awk '{print $2}')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON_CMD="$cmd"
            echo "  [OK] Python $version"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "  [错误] 未找到 Python 3.11+"
    echo "  请安装 Python 3.11+ 或使用 conda 创建环境:"
    echo "    conda create -n SDPJ-System python=3.11"
    echo "    conda activate SDPJ-System"
    exit 1
fi

# --- 安装 Python 依赖 ---
echo ""
echo "[2/4] 安装 Python 依赖..."

$PYTHON_CMD -m pip install --upgrade pip -q
$PYTHON_CMD -m pip install -r requirements.txt -q

echo "  [OK] Python 依赖安装完成"

# --- 检查并安装 Node.js 依赖 ---
echo ""
echo "[3/4] 安装前端依赖..."

FRONTEND_DIR="$SCRIPT_DIR/sdpj/ui/webui/frontend"

if ! command -v node &> /dev/null; then
    echo "  [信息] 未找到 Node.js，正在自动安装..."
    if [ "$(uname)" = "Darwin" ]; then
        if command -v brew &> /dev/null; then
            brew install node@20
            export PATH="/usr/local/opt/node@20/bin:$PATH"
        else
            echo "  [错误] 未找到 Homebrew，请手动安装 Node.js 20+: https://nodejs.org/"
            exit 1
        fi
    elif command -v apt-get &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get update -y
        apt-get install -y nodejs
    elif command -v yum &> /dev/null; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | bash -
        yum install -y nodejs
    else
        echo "  [错误] 无法自动安装 Node.js，请手动安装 Node.js 20+: https://nodejs.org/"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        echo "  [错误] Node.js 安装失败，请手动安装: https://nodejs.org/"
        exit 1
    fi
    echo "  [OK] Node.js 安装完成"
fi

node_version=$(node --version)
echo "  [OK] Node.js $node_version"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "  正在安装前端依赖 (首次安装可能需要几分钟)..."
    (cd "$FRONTEND_DIR" && npm install --silent) || {
        echo "  [错误] 前端依赖安装失败"
        exit 1
    }
fi

echo "  [OK] 前端依赖安装完成"

# --- 初始化配置 ---
echo ""
echo "[4/4] 初始化配置..."

# 复制 .env 文件
if [ ! -f "$SCRIPT_DIR/.env" ] && [ -f "$SCRIPT_DIR/.env.example" ]; then
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    echo "  [OK] 已创建 .env 配置文件"
fi

# 初始化数据库
DB_PATH="$SCRIPT_DIR/sdpj/infrastructure/database/sdpj.db"
if [ ! -f "$DB_PATH" ]; then
    echo "  正在初始化数据库..."
    if $PYTHON_CMD -m sdpj.infrastructure.utils.scripts.seed_data; then
        echo "  [OK] 数据库初始化完成"
    else
        echo "  [警告] 数据库初始化失败，首次启动时会自动初始化"
    fi
else
    echo "  [OK] 数据库已存在"
fi

# 设置执行权限
chmod +x "$SCRIPT_DIR/start.sh" 2>/dev/null || true

# --- 安装完成 ---
echo ""
echo "========================================"
echo "  安装完成!"
echo "========================================"
echo ""
echo "启动方式:"
echo ""
echo "  WebUI 模式 (图形界面):"
echo "    ./start.sh"
echo ""
echo "  CLI 模式 (命令行):"
echo "    sdpj --help"
echo ""
