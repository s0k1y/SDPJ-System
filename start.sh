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
API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
LOG_DIR="$SCRIPT_DIR/logs"

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

# Check curl installation (needed for health checks)
if ! command -v curl &> /dev/null; then
    echo "[Error] curl is not installed or not in PATH"
    echo "Please install curl and try again"
    exit 1
fi

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
echo "[1/3] Stopping processes on ports $API_PORT and $FRONTEND_PORT..."

stop_port_process() {
    local port=$1
    local pids
    pids=$(ss -tlnp sport = :"$port" 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2)

    if [ -n "$pids" ]; then
        for pid in $pids; do
            echo "  Stopping port $port process (PID: $pid)"
            kill -9 "$pid" 2>/dev/null || true
        done
    fi
}

stop_port_process "$API_PORT"
stop_port_process "$FRONTEND_PORT"

# Wait for OS to release ports
echo "  Waiting for ports to be released..."
sleep 2

# Check if ports are still in use
if ss -tln sport = :"$API_PORT" 2>/dev/null | grep -q ":$API_PORT"; then
    echo "[1/3] WARNING: Port $API_PORT still occupied"
    echo "  Trying alternative port..."
    API_PORT=8001
fi

# Check frontend port conflict
for _retry in $(seq 1 5); do
    if ! ss -tln sport = :"$FRONTEND_PORT" 2>/dev/null | grep -q ":$FRONTEND_PORT"; then
        break
    fi
    echo "[1/3] WARNING: Port $FRONTEND_PORT still occupied"
    FRONTEND_PORT=$((FRONTEND_PORT + 1))
    echo "  Trying alternative port: $FRONTEND_PORT"
done

echo "[1/3] Port cleanup done"
echo ""

# --- Step 2: Start backend ---
echo "[2/3] Starting backend service on port $API_PORT..."

mkdir -p "$LOG_DIR"

# Start backend in background, export API_PORT so pydantic_settings picks it up
export API_PORT
nohup "$PYTHON_EXE" -m sdpj.ui.webui.backend.app > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

# Poll for backend readiness by checking health endpoint
echo "  Waiting for backend to be ready..."
BACKEND_READY=false
for i in $(seq 1 15); do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "[2/3] ERROR: Backend service failed to start"
        echo "  Check logs: $LOG_DIR/backend.log"
        exit 1
    fi
    if curl -sk "https://localhost:$API_PORT/health" &>/dev/null; then
        BACKEND_READY=true
        break
    fi
    sleep 1
done

if [ "$BACKEND_READY" != "true" ]; then
    echo "[2/3] ERROR: Backend service did not start within 15 seconds"
    echo "  Check logs: $LOG_DIR/backend.log"
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

# Check if dependencies are installed
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "  node_modules not found, installing dependencies..."
    (cd "$FRONTEND_DIR" && npm install)
    echo "  Dependencies installed"
fi

# Sync backend port to frontend via .env.local
ENV_LOCAL_PATH="$FRONTEND_DIR/.env.local"
echo "VITE_BACKEND_PORT=$API_PORT" > "$ENV_LOCAL_PATH"
echo "  Synced backend port $API_PORT to .env.local"

# Start frontend in background
cd "$FRONTEND_DIR"
# Pass frontend port to vite dev server (handles port conflict fallback)
nohup npm run dev -- --port "$FRONTEND_PORT" > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to start
echo "  Waiting for frontend to be ready..."
FRONTEND_READY=false
for i in $(seq 1 15); do
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "[3/3] ERROR: Frontend service failed to start"
        echo "  Check logs: $LOG_DIR/frontend.log"
        exit 1
    fi
    if ss -tln sport = :"$FRONTEND_PORT" 2>/dev/null | grep -q ":$FRONTEND_PORT"; then
        FRONTEND_READY=true
        break
    fi
    sleep 1
done

if [ "$FRONTEND_READY" != "true" ]; then
    echo "[3/3] ERROR: Frontend service did not start within 15 seconds"
    echo "  Check logs: $LOG_DIR/frontend.log"
    exit 1
fi

echo "[3/3] Frontend service started (PID: $FRONTEND_PID)"
echo ""

# --- Summary ---
echo "========================================"
echo "  Startup Complete!"
echo "========================================"
echo ""
echo "  Backend API:  https://localhost:$API_PORT"
echo "  Frontend:     https://localhost:$FRONTEND_PORT"
echo "  API Docs:     https://localhost:$API_PORT/docs"
echo ""
echo "Logs:"
echo "  Backend:      $LOG_DIR/backend.log"
echo "  Frontend:     $LOG_DIR/frontend.log"
echo ""
echo "Tips:"
echo "  - If frontend cannot connect to backend, check the backend logs"
echo "  - Frontend hot-reloads on code changes"
echo "  - Backend requires manual restart on code changes"
echo ""
echo "To stop the services, run: kill $BACKEND_PID $FRONTEND_PID"
