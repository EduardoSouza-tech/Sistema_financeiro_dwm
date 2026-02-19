# ============================================================================
# SCRIPT POWERSHELL - Limpar Dados Corrompidos do Plano de Contas
# Executa automaticamente o SQL de limpeza no Railway
# ============================================================================

Write-Host "=" -NoNewline
Write-Host ("="*79)
Write-Host "🧹 LIMPEZA DE DADOS CORROMPIDOS - PLANO DE CONTAS" -ForegroundColor Cyan
Write-Host "=" -NoNewline
Write-Host ("="*79)
Write-Host ""

# Verificar se Railway CLI está instalado
$railwayInstalled = Get-Command railway -ErrorAction SilentlyContinue

if (-not $railwayInstalled) {
    Write-Host "❌ Railway CLI não encontrada!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Instale com: npm install -g @railway/cli" -ForegroundColor Yellow
    Write-Host "Ou use o Railway Dashboard: https://railway.app" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host "✅ Railway CLI encontrada" -ForegroundColor Green
Write-Host ""

# SQL de limpeza
$sql = @"
-- Verificar linhas corrompidas
SELECT 
    id, 
    empresa_id, 
    nome_versao, 
    exercicio_fiscal,
    is_ativa
FROM plano_contas_versao
WHERE nome_versao = 'nome_versao'
   OR exercicio_fiscal::text = 'exercicio_fiscal';

-- Deletar linhas corrompidas
DELETE FROM plano_contas_versao
WHERE nome_versao = 'nome_versao'
   OR exercicio_fiscal::text = 'exercicio_fiscal';

-- Verificar resultado
SELECT 
    empresa_id,
    COUNT(*) as total_versoes
FROM plano_contas_versao
GROUP BY empresa_id
ORDER BY empresa_id;
"@

Write-Host "📋 SQL a ser executado:" -ForegroundColor Cyan
Write-Host $sql -ForegroundColor Gray
Write-Host ""

$confirmacao = Read-Host "❓ Deseja executar este SQL no Railway? (s/n)"

if ($confirmacao -ne 's') {
    Write-Host "⏭️ Operação cancelada" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🚀 Conectando ao Railway PostgreSQL..." -ForegroundColor Cyan

# Criar arquivo temporário com SQL
$tempFile = [System.IO.Path]::GetTempFileName() + ".sql"
$sql | Out-File -FilePath $tempFile -Encoding UTF8

Write-Host "📝 SQL salvo em: $tempFile" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️ Aguarde a conexão com o banco de dados..." -ForegroundColor Yellow
Write-Host ""

# Executar via Railway
railway run psql -f $tempFile

# Limpar arquivo temporário
Remove-Item $tempFile -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=" -NoNewline
Write-Host ("="*79)
Write-Host "✅ LIMPEZA CONCLUÍDA!" -ForegroundColor Green
Write-Host "=" -NoNewline
Write-Host ("="*79)
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "   1. Aguardar deploy do Railway (2-3 minutos)"
Write-Host "   2. Limpar cache do navegador (Ctrl+Shift+Delete)"
Write-Host "   3. Recarregar página (Ctrl+F5)"
Write-Host "   4. Testar interface 'Plano de Contas'"
Write-Host "   5. Se vazio, usar botão '📦 Importar Plano Padrão'"
Write-Host ""
