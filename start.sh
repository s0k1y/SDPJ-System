#!/bin/bash

# SDPJ-System Start Script for Linux/macOS
set -e

echo "========================================"
echo "  SDPJ-System Start Script"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
PYTHON_EXE="${PYTHON_PATH:-python}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# Check Python installation
if ! command -v "$PYTHON_EXE" &> /dev/null; then
    echo "[Error] Python is not installed or not in PATH"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$("$PYTHON_EXE" --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo "[Error] Python 3.11+ is required, found Python $PYTHON_VERSION"
    exit 1
fi

echo "[Init] Using Python: $PYTHON_EXE (version $PYTHON_VERSION)"

# --- Init SSL Certificates (via SecureCommManager) ---
echo "[Init] Ensuring SSL certificates via SecureCommManager..."
CERT_INFO=$("$PYTHON_EXE" -c "from sdpj.core.secure_comm_manager import SecureCommManager; m = SecureCommManager(); cert, key = m.ensure_certificates(); print(f'{cert}|{key}')" 2>/dev/null || echo "")

if [ -n "$CERT_INFO" ]; then
    CERT_PATH=$(echo "$CERT_INFO" | cut -d'|' -f1)
    KEY_PATH=$(echo "$CERT_INFO" | cut -d'|' -f2)
    echo "[Init] SSL certificates ready"
else
    echo "[Init] WARNING: Failed to get certificate paths, falling back to certs/"
    CERT_DIR="$SCRIPT_DIR/certs"
    CERT_PATH="$CERT_DIR/cert.pem"
    KEY_PATH="$CERT_DIR/key.pem"
fi
echo ""

# --- Init Database ---
DB_PATH="sdpj/infrastructure/database/sdpj.db"
if [ ! -f "$DB_PATH" ]; then
    echo "[Init] Database not found, initializing..."
    "$PYTHON_EXE" -m sdpj.infrastructure.utils.scripts.seed_data
    echo "[Init] Database initialized"
    echo ""
else
    echo "[Init] Database exists, skipping"
    echo ""
fi

# --- Step 1: Kill processes on target ports ---
echo "[1/3] Stopping processes on ports $BACKEND_PORT and $FRONTEND_PORT..."

stop_port_process() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null || echo "")
    
    if [ -n "$pids" ]; then
        for pid in $pids; do
            echo "  Stopping port $port process (PID: $pid)"
            kill -9 "$pid" 2>/dev/null || true
        done
    fi
}

stop_port_process $BACKEND_PORT
stop_port_process $FRONTEND_PORT

# Wait for OS to release ports
echo "  Waiting for ports to be released..."
sleep 2

# Check if ports are still in use
if lsof -i :$BACKEND_PORT &>/dev/null; then
    echo "[1/3] WARNING: Port $BACKEND_PORT still occupied"
    echo "  Trying alternative port..."
    BACKEND_PORT=8001
fi

echo "[1/3] Port cleanup done"
echo ""

# --- Step 2: Start backend ---
echo "[2/3] Starting backend service on port $BACKEND_PORT..."

# Start backend in background
nohup "$PYTHON_EXE" -m sdpj.ui.webui.backend.app > /dev/null 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "[2/3] ERROR: Backend service failed to start"
    exit 1
fi

echo "[2/3] Backend service started (PID: $BACKEND_PID)"
echo ""

# --- Step 3: Start frontend ---
echo "[3/3] Starting frontend service..."

FRONTEND_DIR="$SCRIPT_DIR/sdpj/ui/webui/frontend"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "[3/3] ERROR: Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Check Node.js installation
if ! command -v node &> /dev/null; then
    echo "[3/3] ERROR: Node.js is not installed"
    echo "Please install Node.js and try again"
    exit 1
fi

# Check npm installation
if ! command -v npm &> /dev/null; then
    echo "[3/3] ERROR: npm is not installed"
    echo "Please install npm and try again"
    exit 1
fi

# Sync backend port to frontend via .env.local
ENV_LOCAL_PATH="$FRONTEND_DIR/.env.local"
echo "VITE_BACKEND_PORT=$BACKEND_PORT" > "$ENV_LOCAL_PATH"
echo "  Synced backend port $BACKEND_PORT to .env.local"

# Start frontend in background
cd "$FRONTEND_DIR"
nohup npm run dev > /dev/null 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 3

# Check if frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "[3/3] ERROR: Frontend service failed to start"
    exit 1
fi

echo "[3/3] Frontend service started (PID: $FRONTEND_PID)"
echo ""

# --- Summary ---
echo "========================================"
echo "  Startup Complete!"
echo "========================================"
echo ""
echo "  Backend API:  https://localhost:$BACKEND_PORT"
echo "  Frontend:     https://localhost:$FRONTEND_PORT"
echo "  API Docs:     https://localhost:$BACKEND_PORT/docs"
echo ""
echo "Tips:"
echo "  - If frontend cannot connect to backend, check the backend logs"
echo "  - Frontend hot-reloads on code changes"
echo "  - Backend requires manual restart on code changes"
echo ""
echo "To stop the services, run: kill $BACKEND_PID $FRONTEND_PID"
