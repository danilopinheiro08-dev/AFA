#!/bin/bash
# AFA - Anti-Fraud Agent Starter (Linux/Mac)

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Iniciando Anti-Fraud Agent..."
echo

# Backend
cd "$BASE_DIR/backend"
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!
echo "[OK] Backend iniciado (PID: $BACKEND_PID)"

# Frontend
cd "$BASE_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "[OK] Frontend iniciado (PID: $FRONTEND_PID)"

echo
echo "=============================================="
echo " 🛡️  Anti-Fraud Agent rodando!"
echo "    Frontend: http://localhost:5173"
echo "    API Docs: http://localhost:8000/docs"
echo " Ctrl+C para encerrar"
echo "=============================================="

wait $BACKEND_PID $FRONTEND_PID
