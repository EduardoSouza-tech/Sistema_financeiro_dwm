# Script de Verificação - Permissões de Regras de Conciliação
# Execute este script após fazer login no sistema

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERIFICAÇÃO DE PERMISSÕES - REGRAS" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 INSTRUÇÕES:" -ForegroundColor White
Write-Host ""
Write-Host "1. Abra o sistema no navegador:" -ForegroundColor White
Write-Host "   https://sistemafinanceirodwm-production.up.railway.app" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Faça login no sistema" -ForegroundColor White
Write-Host ""
Write-Host "3. Abra o Console do navegador (F12)" -ForegroundColor White
Write-Host ""
Write-Host "4. Digite e execute:" -ForegroundColor White
Write-Host "   console.log('Permissões:', permissoesUsuario)" -ForegroundColor Yellow
Write-Host ""
Write-Host "5. Verifique se aparece as permissões:" -ForegroundColor White
Write-Host "   • regras_conciliacao_view" -ForegroundColor Green
Write-Host "   • regras_conciliacao_create" -ForegroundColor Green
Write-Host "   • regras_conciliacao_edit" -ForegroundColor Green
Write-Host "   • regras_conciliacao_delete" -ForegroundColor Green
Write-Host ""
Write-Host "6. Clique em 'Extrato Bancário' no menu" -ForegroundColor White
Write-Host ""
Write-Host "7. Clique no botão 'Configurações' (ícone de engrenagem)" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Se as etapas 6 e 7 funcionarem:" -ForegroundColor Green
Write-Host "   TUDO ESTÁ CORRETO!" -ForegroundColor Green
Write-Host ""
Write-Host "❌ Se ainda aparecer erro 403:" -ForegroundColor Red
Write-Host "   1. Faça LOGOUT do sistema" -ForegroundColor Yellow
Write-Host "   2. Faça LOGIN novamente" -ForegroundColor Yellow
Write-Host "   3. Tente novamente" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
