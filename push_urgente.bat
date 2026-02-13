@echo off
echo ===================================
echo PUSH URGENTE - Correcao de Eventos
echo ===================================
echo.
cd /d "%~dp0"
echo Tentativa 1...
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================
    echo SUCESSO! Push realizado!
    echo ===================================
    pause
    exit /b 0
)

echo.
echo Tentativa 1 falhou. Aguardando 3 segundos...
timeout /t 3 /nobreak > nul

echo Tentativa 2...
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================
    echo SUCESSO! Push realizado!
    echo ===================================
    pause
    exit /b 0
)

echo.
echo Tentativa 2 falhou. Aguardando 5 segundos...
timeout /t 5 /nobreak > nul

echo Tentativa 3...
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================
    echo SUCESSO! Push realizado!
    echo ===================================
    pause
    exit /b 0
)

echo.
echo ===================================
echo ERRO: Todas as 3 tentativas falharam
echo Verifique sua conexao ou firewall
echo ===================================
pause
