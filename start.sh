#!/usr/bin/env bash
# =============================================================================
# ATS Resume Checker — Start Script
# =============================================================================
# Usage:
#   ./start.sh          Start the server (builds frontend if needed)
#   ./start.sh stop     Stop the running server
#   ./start.sh restart  Restart the server
#   ./start.sh status   Show server status + URL
#   ./start.sh logs     Tail live server logs
# =============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$ROOT/.server.pid"
LOGFILE="$ROOT/server.log"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
VENV="$ROOT/.venv"
PORT=8000

# ── Helpers ──────────────────────────────────────────────────────────────────

red()   { echo -e "\033[31m$*\033[0m"; }
green() { echo -e "\033[32m$*\033[0m"; }
yellow(){ echo -e "\033[33m$*\033[0m"; }
blue()  { echo -e "\033[34m$*\033[0m"; }

is_running() {
    if [[ -f "$PIDFILE" ]]; then
        local pid
        pid=$(cat "$PIDFILE")
        kill -0 "$pid" 2>/dev/null && return 0
    fi
    return 1
}

stop_server() {
    if is_running; then
        local pid
        pid=$(cat "$PIDFILE")
        yellow "Stopping server (PID $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 1
        rm -f "$PIDFILE"
        green "Server stopped."
    else
        # Also kill anything on the port
        local pid_on_port
        pid_on_port=$(lsof -ti :"$PORT" 2>/dev/null || true)
        if [[ -n "$pid_on_port" ]]; then
            kill -9 "$pid_on_port" 2>/dev/null || true
            yellow "Killed stale process on port $PORT."
        else
            yellow "Server is not running."
        fi
    fi
}

# ── Commands ─────────────────────────────────────────────────────────────────

CMD="${1:-start}"

case "$CMD" in

  stop)
    stop_server
    ;;

  restart)
    stop_server
    sleep 1
    exec "$0" start
    ;;

  status)
    if is_running; then
    pid=""
        pid=$(cat "$PIDFILE")
        green "✅ Server is running (PID $pid)"
        blue "   http://localhost:$PORT"
    else
        red "❌ Server is not running."
        echo "   Run: ./start.sh"
    fi
    ;;

  logs)
    if [[ -f "$LOGFILE" ]]; then
        tail -f "$LOGFILE"
    else
        red "No log file found at $LOGFILE"
    fi
    ;;

  start)
    # ── Pre-flight checks ───────────────────────────────────────────────

    # Stop any existing server first
    if is_running; then
        yellow "Server already running. Restarting..."
        stop_server
        sleep 1
    else
        # Kill anything stale on the port
        pid_on_port=""
        pid_on_port=$(lsof -ti :"$PORT" 2>/dev/null || true)
        if [[ -n "$pid_on_port" ]]; then
            kill -9 "$pid_on_port" 2>/dev/null || true
        fi
    fi

    # Ensure .env exists
    if [[ ! -f "$ROOT/.env" ]]; then
        if [[ -f "$ROOT/.env.example" ]]; then
            yellow "⚠️  No .env found. Copying from .env.example..."
            cp "$ROOT/.env.example" "$ROOT/.env"
            red "   ‼️  Edit .env and add your GEMINI_API_KEY, then run ./start.sh again."
            exit 1
        else
            red "❌ No .env file found. Create one with GEMINI_API_KEY set."
            exit 1
        fi
    fi

    # Ensure venv exists
    if [[ ! -f "$VENV/bin/uvicorn" ]]; then
        yellow "🐍 Virtual environment missing. Creating..."
        python3 -m venv "$VENV"
        "$VENV/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"
        green "   Dependencies installed."
    fi

    # ── Build frontend ──────────────────────────────────────────────────
    DIST_DIR="$FRONTEND_DIR/dist"
    if [[ ! -d "$DIST_DIR" ]]; then
        blue "🔨 Building frontend..."
        (cd "$FRONTEND_DIR" && npm install --silent && npm run build)
        green "   Frontend built: $DIST_DIR"
    else
        blue "✅ Frontend build already exists. (run 'rm -rf frontend/dist && ./start.sh' to rebuild)"
    fi

    # ── Start backend (serves both API + frontend) ──────────────────────
    blue "🚀 Starting server on http://localhost:$PORT ..."
    cd "$BACKEND_DIR"
    nohup "$VENV/bin/uvicorn" main:app --host 0.0.0.0 --port "$PORT" \
        >> "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 2

    if is_running; then
        green "✅ Server started (PID $(cat "$PIDFILE"))"
        green "   Open: http://localhost:$PORT"
        echo ""
        blue "   Logs:    tail -f $LOGFILE"
        blue "   Stop:    ./start.sh stop"
        blue "   Restart: ./start.sh restart"
    else
        red "❌ Server failed to start. Check logs:"
        tail -20 "$LOGFILE"
        exit 1
    fi
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status|logs}"
    exit 1
    ;;
esac
