@echo off
chcp 65001 >nul
cd /d "%~dp0"
git add -A
git commit -m "fix: adicionar campo contrato_id em sessoes e exibir numero do contrato"
git push
echo.
echo Deploy concluido! Aguarde 60s para Railway processar...
timeout /t 60 /nobreak
