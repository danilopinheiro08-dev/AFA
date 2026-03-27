@echo off
setlocal EnableDelayedExpansion
title Anti-Fraud Agent (AFA) - Instalador

echo =============================================
echo  Anti-Fraud Agent (AFA) - Instalador Windows
echo =============================================
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Baixe em https://python.org
    pause & exit /b 1
)

:: Verifica Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado. Baixe em https://nodejs.org
    pause & exit /b 1
)

echo [OK] Python e Node.js encontrados
echo.

:: Configura backend
echo [1/4] Configurando ambiente Python...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt -q
echo [OK] Dependencias Python instaladas

:: Copia .env se nao existir
if not exist .env (
    copy .env.example .env
    echo [AVISO] Arquivo .env criado. Configure sua GROQ_API_KEY em backend\.env
    echo         Ou troque LLM_PROVIDER=ollama para uso 100%% local
)
cd ..

:: Configura frontend
echo.
echo [2/4] Instalando dependencias frontend...
cd frontend
call npm install --silent
cd ..
echo [OK] Frontend configurado

:: Cria data dirs
echo.
echo [3/4] Criando pastas de dados...
mkdir backend\data\csv 2>nul
mkdir backend\data\chroma 2>nul
mkdir backend\data\reports 2>nul
mkdir backend\data\blacklist 2>nul
echo [OK] Estrutura de dados criada

echo.
echo [4/4] Verificando configuracao Ollama (opcional para uso local)...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Ollama nao encontrado. Instale em https://ollama.com se preferir LLM local.
    echo        O sistema esta configurado para usar Groq API por padrao.
) else (
    echo [OK] Ollama encontrado
    echo [INFO] Para baixar o modelo Qwen: ollama pull qwen2.5:7b
)

echo.
echo =============================================
echo  Instalacao concluida!
echo.
echo  Para iniciar o sistema, execute:  start.bat
echo.
echo  IMPORTANTE: Configure sua GROQ_API_KEY em:
echo  backend\.env
echo =============================================
pause
