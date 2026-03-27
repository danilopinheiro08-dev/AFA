@echo off
title Anti-Fraud Agent - Iniciando...

echo Iniciando Anti-Fraud Agent...
echo.

:: Backend
start "AFA - Backend" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Aguarda backend iniciar
timeout /t 4 /nobreak >nul

:: Frontend
start "AFA - Frontend" cmd /k "cd frontend && npm run dev"

:: Aguarda e abre navegador
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo [OK] Anti-Fraud Agent rodando em http://localhost:5173
echo [OK] API disponivel em http://localhost:8000/docs
echo.
echo Feche as janelas de terminal para encerrar.
