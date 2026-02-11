Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🔍 DIAGNÓSTICO - CRIAÇÃO DE REGRA DE CONCILIAÇÃO      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$url = "https://sistemafinanceirodwm-production.up.railway.app"

# 1. Aguardar deploy
Write-Host "⏳ Aguardando 90 segundos para o deploy..." -ForegroundColor Yellow
Start-Sleep -Seconds 90

# 2. Verificar estrutura da tabela
Write-Host "`n📊 1. VERIFICANDO ESTRUTURA DA TABELA..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$url/api/debug/verificar-tabela-regras" -Method Get -TimeoutSec 30
    
    Write-Host "✅ Tabela existe: $($response.tabela_existe)" -ForegroundColor Green
    
    if ($response.tabela_existe) {
        Write-Host "`n📋 Colunas da tabela:" -ForegroundColor White
        foreach ($col in $response.colunas) {
            Write-Host "   • $($col.column_name): $($col.data_type) | Nullable: $($col.is_nullable)" -ForegroundColor Gray
        }
        
        Write-Host "`n📊 Total de regras: $($response.total_regras)" -ForegroundColor White
        
        # Verificar se usa_integracao_folha ainda existe
        $coluna_existe = $response.colunas | Where-Object { $_.column_name -eq 'usa_integracao_folha' }
        if ($coluna_existe) {
            Write-Host "`n⚠️  PROBLEMA ENCONTRADO!" -ForegroundColor Red
            Write-Host "   A coluna 'usa_integracao_folha' ainda existe na tabela" -ForegroundColor Red
            Write-Host "   Essa coluna deveria ter sido removida pela migration" -ForegroundColor Red
        } else {
            Write-Host "`n✅ Coluna 'usa_integracao_folha' não existe (correto!)" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "❌ Erro ao verificar tabela: $_" -ForegroundColor Red
}

# 3. Executar script Python de teste
Write-Host "`n💾 2. EXECUTANDO TESTE DE CRIAÇÃO NO BANCO..." -ForegroundColor Cyan
try {
    python testar_criar_regra.py
} catch {
    Write-Host "❌ Erro ao executar script Python: $_" -ForegroundColor Red
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   📝 INSTRUÇÕES PARA CONTINUAR                           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  Tente criar uma regra novamente no sistema" -ForegroundColor White
Write-Host "    → Acesse: $url" -ForegroundColor Gray
Write-Host "    → Vá em 💰 Financeiro > 🏦 Extrato Bancário" -ForegroundColor Gray
Write-Host "    → Clique em ⚙️ Configurações" -ForegroundColor Gray
Write-Host "    → Tente criar uma regra" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  Abra o Railway Logs ANTES de salvar" -ForegroundColor White
Write-Host "    → https://railway.app/project/SEU_PROJECT/deployments" -ForegroundColor Gray
Write-Host "    → Clique em 'View Logs'" -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  Copie TODOS os logs que aparecerem após clicar em Salvar" -ForegroundColor White
Write-Host "    → Procure por linhas com [criar_regra]" -ForegroundColor Gray
Write-Host "    → Me envie os logs completos" -ForegroundColor Gray
Write-Host ""
