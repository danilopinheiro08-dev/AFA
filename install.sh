#!/bin/bash

# ==============================================
# Anti-Fraud Agent (AFA) - Instalador
# ==============================================

# Garante que o script roda a partir do diretório do repositório
cd "$(dirname "$0")"

echo "=============================================="
echo " Anti-Fraud Agent (AFA) - Instalador"
echo "=============================================="

# Configurar diretório temporário para evitar Erro 28 (/tmp cheio)
export TMPDIR="$HOME/.cache/afa_tmp"
export PIP_CACHE_DIR="$HOME/.cache/pip"
mkdir -p "$TMPDIR"

# Verificar dependências
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python 3 não encontrado."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "[ERRO] Node.js não encontrado."
    exit 1
fi

echo "[OK] Python e Node.js encontrados"

# 1. Backend
echo ""
echo "[1/4] Configurando ambiente Python..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
# Usar TMPDIR explicitamente para segurança
TMPDIR="$TMPDIR" pip install -r requirements.txt -q
cd ..

# 2. Frontend
echo ""
echo "[2/4] Instalando dependências do Frontend (isso pode levar uns minutos)..."
cd frontend
npm install --silent
cd ..

# 3. Data dirs
echo ""
echo "[3/4] Criando diretórios de dados..."
mkdir -p backend/data/csv
mkdir -p backend/data/chroma
mkdir -p backend/data/reports
mkdir -p backend/data/blacklist

# 4. Finalização
echo ""
echo "[4/4] Concluído!"
echo "----------------------------------------------"
echo "Para iniciar a aplicação:"
echo "1. Configure o arquivo 'backend/.env' (veja .env.example)"
echo "2. Execute './start.sh'"
echo "----------------------------------------------"
echo "Nota: Se o sistema reclamar de falta de espaço, agora ele usa $HOME/.cache/afa_tmp."
