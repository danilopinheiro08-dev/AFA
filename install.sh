#!/bin/bash
# AFA - Anti-Fraud Agent Installer (Linux/Mac)

set -e

echo "=============================================="
echo " Anti-Fraud Agent (AFA) - Instalador"
echo "=============================================="
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python3 não encontrado. Instale com: sudo apt install python3 python3-venv"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "[ERRO] Node.js não encontrado. Instale em: https://nodejs.org"
    exit 1
fi

echo "[OK] Python e Node.js encontrados"
echo

# Backend
echo "[1/4] Configurando ambiente Python..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
echo "[OK] Dependências instaladas"

if [ ! -f .env ]; then
    cp .env.example .env
    echo "[AVISO] Arquivo .env criado. Configure sua GROQ_API_KEY em backend/.env"
fi
cd ..

# Frontend
echo
echo "[2/4] Instalando dependências frontend..."
cd frontend
npm install --silent
cd ..
echo "[OK] Frontend configurado"

# Data dirs
echo
echo "[3/4] Criando pastas de dados..."
mkdir -p backend/data/{csv,chroma,reports,blacklist}
echo "[OK] Estrutura criada"

# Ollama
echo
echo "[4/4] Verificando Ollama (opcional)..."
if command -v ollama &> /dev/null; then
    echo "[OK] Ollama encontrado"
else
    echo "[INFO] Ollama não encontrado. Instale em https://ollama.com para LLM 100% local."
fi

echo
echo "=============================================="
echo " Instalação concluída!"
echo " Execute: ./start.sh"
echo
echo " Configure sua GROQ_API_KEY em: backend/.env"
echo "=============================================="
