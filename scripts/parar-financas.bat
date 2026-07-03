@echo off
chcp 65001 >nul
title Parar Sistema Financas

echo.
echo ============================================================
echo   Parando Sistema de Financas Pessoais...
echo ============================================================
echo.

REM Mata processos do backend (uvicorn/python rodando na porta 8080)
echo [1/2] Parando backend...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Mata processos do frontend (node rodando na porta 5173)
echo [2/2] Parando frontend...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ✅ Sistema parado.
echo.
timeout /t 3 /nobreak >nul
exit