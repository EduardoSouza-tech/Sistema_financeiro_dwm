Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   📋 LISTAR REGRAS DE CONCILIAÇÃO EXISTENTES             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$url = "https://sistemafinanceirodwm-production.up.railway.app"

Write-Host "🔍 Buscando regras cadastradas..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "$url/api/regras-conciliacao" -Method Get -TimeoutSec 30
    
    Write-Host "✅ $($response.Count) regra(s) encontrada(s)" -ForegroundColor Green
    Write-Host ""
    
    $i = 1
    foreach ($regra in ($response | Sort-Object empresa_id, palavra_chave)) {
        Write-Host "[$i] ID: $($regra.id) | Empresa: $($regra.empresa_id)" -ForegroundColor White
        Write-Host "    🔤 Palavra-chave: $($regra.palavra_chave)" -ForegroundColor Cyan
        
        if ($regra.categoria) {
            Write-Host "    📁 $($regra.categoria) → $($regra.subcategoria)" -ForegroundColor Gray
        }
        
        Write-Host ""
        $i++
    }
    
    # Verificar duplicatas
    Write-Host "🔍 Verificando duplicatas..." -ForegroundColor Cyan
    $grupos = $response | Group-Object -Property palavra_chave,empresa_id
    $duplicatas = @()
    
    foreach ($grupo in $grupos) {
        if ($grupo.Count -gt 1) {
            $duplicatas += $grupo
        }
    }
    
    if ($duplicatas.Count -gt 0) {
        Write-Host "⚠️  $($duplicatas.Count) duplicata(s) encontrada(s)!" -ForegroundColor Red
    }
    else {
        Write-Host "✅ Nenhuma duplicata encontrada!" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Erro: $_" -ForegroundColor Red
}

Write-Host ""
