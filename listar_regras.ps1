Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   📋 LISTAR REGRAS DE CONCILIAÇÃO EXISTENTES             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$url = "https://sistemafinanceirodwm-production.up.railway.app"

# Listar regras via API
Write-Host "🔍 Buscando regras cadastradas..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$url/api/regras-conciliacao" -Method Get -TimeoutSec 30
    
    $regras = $response
    if ($regras -is [PSCustomObject] -and $regras.data) {
        $regras = $regras.data
    }
    
    if ($regras.Count -eq 0) {
        Write-Host "⚠️  Nenhuma regra cadastrada ainda." -ForegroundColor Yellow
    }
    else {
        Write-Host "✅ $($regras.Count) regra(s) encontrada(s)" -ForegroundColor Green
        Write-Host ""
        
        $empresaAtual = $null
        $i = 1
        
        foreach ($regra in ($regras | Sort-Object empresa_id, palavra_chave)) {
            # Separador por empresa
            if ($regra.empresa_id -ne $empresaAtual) {
                $empresaAtual = $regra.empresa_id
                Write-Host "================================================================================" -ForegroundColor Gray
                Write-Host "🏢 EMPRESA ID: $($regra.empresa_id)" -ForegroundColor White
                Write-Host "================================================================================" -ForegroundColor Gray
            }
            
            $status = if ($regra.ativo) { "✅ ATIVA" } else { "❌ INATIVA" }
            
            Write-Host ""
            Write-Host "[$i] $status | ID: $($regra.id)" -ForegroundColor White
            Write-Host "    🔤 Palavra-chave: $($regra.palavra_chave)" -ForegroundColor Cyan
            
            if ($regra.categoria) {
                Write-Host "    📁 Categoria: $($regra.categoria) → $($regra.subcategoria)" -ForegroundColor Gray
            }
            
            if ($regra.cliente_padrao) {
                Write-Host "    👤 Cliente/Fornecedor: $($regra.cliente_padrao)" -ForegroundColor Gray
            }
            
            if ($regra.descricao) {
                Write-Host "    📝 Descrição: $($regra.descricao)" -ForegroundColor Gray
            }
            
            $i++
        }
        
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Gray
        Write-Host ""
        
        # Verificar duplicatas
        Write-Host "🔍 VERIFICANDO DUPLICATAS..." -ForegroundColor Cyan
        
        $grupos = $regras | Group-Object -Property @{Expression={$_.empresa_id.ToString() + "_" + $_.palavra_chave}}
        $duplicatas = $grupos | Where-Object { $_.Count -gt 1 }
        
        if ($duplicatas) {
            Write-Host ""
            Write-Host "⚠️  ATENÇÃO: $($duplicatas.Count) palavra(s)-chave duplicada(s) encontrada(s)!" -ForegroundColor Red
            Write-Host ""
            
            foreach ($dup in $duplicatas) {
                $primeiraRegra = $dup.Group[0]
                Write-Host "   • Empresa $($primeiraRegra.empresa_id): '$($primeiraRegra.palavra_chave)' ($($dup.Count)x)" -ForegroundColor Yellow
                $ids = ($dup.Group.id | ForEach-Object { $_.ToString() }) -join ', '
                Write-Host "     IDs: $ids" -ForegroundColor Gray
            }
            
            Write-Host ""
            Write-Host "💡 Para remover duplicatas:" -ForegroundColor White
            Write-Host "   1. Acesse o sistema: $url" -ForegroundColor Gray
            Write-Host "   2. Vá em 💰 Financeiro > 🏦 Extrato Bancário > ⚙️ Configurações" -ForegroundColor Gray
            Write-Host "   3. Exclua as regras duplicadas (manter apenas uma)" -ForegroundColor Gray
        }
        else {
            Write-Host "✅ Nenhuma duplicata encontrada!" -ForegroundColor Green
        }
    }
    
}
catch {
    Write-Host "❌ Erro ao buscar regras: $_" -ForegroundColor Red
}

Write-Host ""
