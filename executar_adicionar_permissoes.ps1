# Script para adicionar permissões de regras no Railway
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ADICIONAR PERMISSÕES - RAILWAY" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Executando script no Railway..." -ForegroundColor White
railway run python adicionar_permissoes_empresa.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " CONCLUÍDO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
