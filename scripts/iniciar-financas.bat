@echo off
chcp 65001 >nul
title Iniciador - Sistema Financas Pessoais

REM ========================================
REM Versao melhorada do iniciador
REM - Mata processos antigos antes de subir
REM - Mostra as janelas do backend e frontend
REM - Espera mais tempo para garantir startup
REM ========================================

cd /d "%~dp0\.."

echo.
echo ============================================================
echo   Iniciando Sistema de Financas Pessoais...
echo ============================================================
echo.

REM ============================================================
REM PASSO 0: Mata processos antigos (evita erro de porta em uso)
REM ============================================================
echo [0/4] Limpando processos antigos...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM ============================================================
REM PASSO 1: Inicia BACKEND (janela VISIVEL)
REM ============================================================
echo [1/4] Iniciando backend (porta 8080)...
start "Backend Financas" cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --port 8080"

REM Aguarda 8 segundos para o backend subir
echo [2/4] Aguardando backend ficar pronto (8s)...
timeout /t 8 /nobreak >nul

REM ============================================================
REM PASSO 2: Inicia FRONTEND (janela VISIVEL)
REM ============================================================
echo [3/4] Iniciando frontend (porta 5173)...
start "Frontend Financas" cmd /k "cd frontend && npm run dev"

REM Aguarda 6 segundos para o frontend compilar
echo [4/4] Aguardando frontend compilar (6s)...
timeout /t 6 /nobreak >nul

REM ============================================================
REM PASSO 3: Abre o navegador
REM ============================================================
echo.
echo Abrindo navegador...
start http://localhost:5173

echo.
echo ============================================================
echo   Sistema iniciado!
echo ============================================================
echo.
echo NAO FECHE as janelas "Backend Financas" e "Frontend Financas"
echo Para parar o sistema, use o arquivo: parar-financas.bat
echo.
echo Esta janela vai fechar em 5 segundos...

timeout /t 5 /nobreak >nul
exit