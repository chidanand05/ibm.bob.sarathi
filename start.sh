#!/bin/bash
# ParallaX | Bengaluru Road Safety Intelligence Platform
# Startup Script — starts backend (port 8000) + frontend (port 3000)

set -e
WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
echo "=== ParallaX Road Safety Intelligence Platform ==="
echo "    Team: ParallaX | IBM Hackathon | Problem Statement 8"
echo "    Workspace: $WORKSPACE"
echo ""

# --- BACKEND ---
echo "[1/3] Starting backend..."
cd "$WORKSPACE"
if [ ! -d "venv" ]; then
  echo "  Creating Python virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r backend/requirements.txt -q

# Run data ingestion if DB is empty
python3 -c "
import sys; sys.path.insert(0,'.')
from backend.database.db import engine, SessionLocal, Base
from backend.database.models import AccidentStatistic
Base.metadata.create_all(bind=engine)
db = SessionLocal()
count = db.query(AccidentStatistic).count()
db.close()
if count == 0:
    print('  Running data ingestion...')
    from backend.database.ingestion import run_all_ingestion
    run_all_ingestion()
else:
    print(f'  Database ready: {count} records found')
"

# Start backend in background
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  Backend started (PID $BACKEND_PID) → http://localhost:8000"
echo "  API docs → http://localhost:8000/api/docs"

# --- FRONTEND ---
echo ""
echo "[2/3] Starting frontend..."
cd "$WORKSPACE/frontend"
if [ ! -d "node_modules" ]; then
  echo "  Installing npm dependencies..."
  npm install --legacy-peer-deps -q
fi

npm run dev &
FRONTEND_PID=$!
echo "  Frontend started (PID $FRONTEND_PID) → http://localhost:3000"

# --- DONE ---
echo ""
echo "[3/3] Platform ready!"
echo ""
echo "  🌐 Dashboard:    http://localhost:3000"
echo "  📡 Backend API:  http://localhost:8000"
echo "  📖 API Docs:     http://localhost:8000/api/docs"
echo ""
echo "  Press Ctrl+C to stop both servers."

wait $BACKEND_PID $FRONTEND_PID
