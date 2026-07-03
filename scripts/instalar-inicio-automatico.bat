@echo off
chcp 65001 >nul
title Instalar Inicio Automatico

echo.
echo ============================================================
echo   Configurar Sistema para iniciar com o Windows
echo ============================================================
echo.

cd /d "%~dp0\.."
set "PROJETO=%CD%"
set "BAT_INICIAR=%PROJETO%\scripts\iniciar-financas.bat"

REM Pasta onde o Windows procura programas para iniciar com o sistema
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

REM Cria atalho do .bat na pasta de inicializacao
echo Criando atalho em: %STARTUP%
echo.

powershell.exe -ExecutionPolicy Bypass -NoProfile -Command ^
  "$WshShell = New-Object -ComObject WScript.Shell; ^
   $Shortcut = $WshShell.CreateShortcut('%STARTUP%\Financas Pessoais.lnk'); ^
   $Shortcut.TargetPath = '%BAT_INICIAR%'; ^
   $Shortcut.WorkingDirectory = '%PROJETO%'; ^
   $Shortcut.WindowStyle = 7; ^
   $Shortcut.Save()"

echo.
echo ✅ Pronto!
echo.
echo O sistema vai iniciar automaticamente toda vez que voce ligar o PC.
echo.
echo Para REMOVER esta funcionalidade depois, basta deletar este arquivo:
echo %STARTUP%\Financas Pessoais.lnk
echo.
pause