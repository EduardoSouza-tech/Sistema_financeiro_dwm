@echo off
chcp 65001 >nul
echo ================================================================================
echo EXECUTANDO MIGRATION REMESSA PAGAMENTO SICREDI
echo ================================================================================

set PYTHON=C:\Users\Nasci\OneDrive\Documents\Programas VS Code\DWM\sistema_financeiro\.venv\Scripts\python.exe

if not exist "%PYTHON%" (
    echo ERRO: Python nao encontrado em %PYTHON%
    pause
    exit /b 1
)

echo.
echo Executando migration...
echo.

"%PYTHON%" executar_migration_remessa_AGORA.py

echo.
pause
