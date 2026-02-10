# 🧪 TESTE APÓS DEPLOY - Regras de Conciliação

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║    🧪 TESTE DE REGRAS DE CONCILIAÇÃO                      ║" -ForegroundColor Cyan  
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "⏳ Aguardando deploy (60 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

Write-Host ""
Write-Host "✅ Deploy concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 INSTRUÇÕES PARA TESTE:" -ForegroundColor White
Write-Host ""
Write-Host "1️⃣  No sistema, vá em:" -ForegroundColor White
Write-Host "   💰 Financeiro → 🏦 Extrato Bancário → ⚙️ Configurações" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  Abra o Console do navegador (F12)" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  Aguarde os logs aparecerem:" -ForegroundColor White
Write-Host ""
Write-Host "   ✅ LOGS ESPERADOS:" -ForegroundColor Green
Write-Host "      🔍 [DEBUG] Iniciando listar_regras_conciliacao" -ForegroundColor Gray
Write-Host "      🔍 [DEBUG] empresa_id: 20" -ForegroundColor Gray
Write-Host "      🔍 [DEBUG] Chamando db.listar_regras_conciliacao..." -ForegroundColor Gray
Write-Host "      ✅ [DEBUG] Regras retornadas: 0" -ForegroundColor Gray
Write-Host ""
Write-Host "   ❌ SE APARECER ERRO:" -ForegroundColor Red
Write-Host "      ❌ [DEBUG] ERRO: [mensagem do erro]" -ForegroundColor Gray
Write-Host "      Copie a mensagem de erro completa!" -ForegroundColor Yellow
Write-Host ""
Write-Host "4️⃣  Tente criar uma regra:" -ForegroundColor White
Write-Host "   - Clique em 'Nova Regra'" -ForegroundColor Gray
Write-Host "   - Preencha os campos" -ForegroundColor Gray
Write-Host "   - Clique em 'Salvar'" -ForegroundColor Gray
Write-Host ""
Write-Host "5️⃣  Verifique os logs no Console:" -ForegroundColor White
Write-Host ""
Write-Host "   ✅ LOGS ESPERADOS:" -ForegroundColor Green
Write-Host "      🔍 [DEBUG] Iniciando criar_regra_conciliacao" -ForegroundColor Gray
Write-Host "      🔍 [DEBUG] empresa_id: 20" -ForegroundColor Gray
Write-Host "      🔍 [DEBUG] Dados recebidos: {...}" -ForegroundColor Gray
Write-Host "      🔍 [DEBUG] Chamando db.criar_regra_conciliacao" -ForegroundColor Gray
Write-Host "      ✅ [DEBUG] Regra criada: {...}" -ForegroundColor Gray
Write-Host ""
Write-Host "   ❌ SE APARECER ERRO:" -ForegroundColor Red
Write-Host "      ❌ [DEBUG] ERRO: [mensagem do erro]" -ForegroundColor Gray
Write-Host "      Copie a mensagem de erro completa!" -ForegroundColor Yellow
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  📸 ENVIE OS LOGS DO CONSOLE                              ║" -ForegroundColor Cyan
Write-Host "║  Isso me ajudará a identificar o problema exato!          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
