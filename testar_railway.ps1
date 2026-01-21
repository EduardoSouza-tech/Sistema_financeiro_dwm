# Script PowerShell para testar Railway
$BASE_URL = "https://sistema-financeiro-dwm-production.up.railway.app"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " TESTE DE RAILWAY - PRODUCAO" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$loginBody = @{
    email = "admin@dwm.com"
    senha = "admin123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$BASE_URL/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.token
    Write-Host "Login bem-sucedido!" -ForegroundColor Green
    Write-Host "Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
}
catch {
    Write-Host "Erro no login: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Teste 1: Login
Write-Host "Fazendo login..." -ForegroundColor White

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host " TESTE 2: Performance Stats" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

$result = Test-Endpoint -Url "$BASE_URL/api/performance/stats" -Token $token

if ($result.Success) {
    Write-Host "✅ Status: OK" -ForegroundColor Green
    Write-Host "⏱️  Tempo: $($result.Tempo)ms" -ForegroundColor Cyan
    
    if ($result.Response.cache) {
        Write-Host ""
        Write-Host "💾 CACHE:" -ForegroundColor Magenta
        Write-Host "   Total de chaves: $($result.Response.cache.total_keys)" -ForegroundColor Gray
        Write-Host "   Chaves válidas: $($result.Response.cache.valid_keys)" -ForegroundColor Gray
        Write-Host "   Taxa de hit: $($result.Response.cache.hit_rate_percent)%" -ForegroundColor Gray
    }
    
    if ($result.Response.queries) {
        Write-Host ""
        Write-Host "🔍 QUERIES:" -ForegroundColor Magenta
        Write-Host "   Total: $($result.Response.queries.total_queries)" -ForegroundColor Gray
        Write-Host "   Tempo médio: $([math]::Round($result.Response.queries.avg_time_ms, 2))ms" -ForegroundColor Gray
        Write-Host "   Queries lentas: $($result.Response.queries.slow_queries)" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ Erro: $($result.Error)" -ForegroundColor Red
}

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host " TESTE 3: Benchmark de Endpoints" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

$endpoints = @(
    @{Nome="Dashboard"; Path="/api/relatorios/dashboard-completo"},
    @{Nome="Lançamentos"; Path="/api/lancamentos"},
    @{Nome="Clientes"; Path="/api/clientes"},
    @{Nome="Fornecedores"; Path="/api/fornecedores"},
    @{Nome="Contratos"; Path="/api/contratos"}
)

$resultados = @()

foreach ($endpoint in $endpoints) {
    Write-Host "`n📊 Testando $($endpoint.Nome)... " -NoNewline -ForegroundColor White
    
    $result = Test-Endpoint -Url "$BASE_URL$($endpoint.Path)" -Token $token
    
    if ($result.Success) {
        $status = if ($result.Tempo -lt 200) { "✅" } elseif ($result.Tempo -lt 500) { "⚠️" } else { "❌" }
        $statusText = if ($result.Tempo -lt 200) { "OK" } elseif ($result.Tempo -lt 500) { "LENTO" } else { "CRÍTICO" }
        
        Write-Host "$status $($result.Tempo)ms" -ForegroundColor $(if ($result.Tempo -lt 200) { "Green" } elseif ($result.Tempo -lt 500) { "Yellow" } else { "Red" })
        
        $resultados += @{
            Nome = $endpoint.Nome
            Tempo = $result.Tempo
            Status = $statusText
        }
    } else {
        Write-Host "❌ Erro" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host " RESUMO DOS TESTES" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan

if ($resultados.Count -gt 0) {
    Write-Host ""
    Write-Host "⏱️  Tempos de Resposta:" -ForegroundColor White
    Write-Host "{0,-20} {1,-15} {2,-10}" -f "Endpoint", "Tempo", "Status"
    Write-Host ("-" * 45)
    
    foreach ($r in $resultados) {
        $cor = if ($r.Status -eq "OK") { "Green" } elseif ($r.Status -eq "LENTO") { "Yellow" } else { "Red" }
        Write-Host ("{0,-20} {1,8}ms     {2,-10}" -f $r.Nome, $r.Tempo, $r.Status) -ForegroundColor $cor
    }
    
    $tempos = $resultados | ForEach-Object { $_.Tempo }
    $media = ($tempos | Measure-Object -Average).Average
    $min = ($tempos | Measure-Object -Minimum).Minimum
    $max = ($tempos | Measure-Object -Maximum).Maximum
    
    Write-Host ""
    Write-Host "📈 Estatísticas:" -ForegroundColor White
    Write-Host "   Média: $([math]::Round($media, 2))ms" -ForegroundColor Gray
    Write-Host "   Mínimo: $([math]::Round($min, 2))ms" -ForegroundColor Gray
    Write-Host "   Máximo: $([math]::Round($max, 2))ms" -ForegroundColor Gray
    
    $abaixo200 = ($tempos | Where-Object { $_ -lt 200 }).Count
    $percentual = ($abaixo200 / $tempos.Count) * 100
    
    Write-Host ""
    Write-Host "🎯 Meta de Performance (<200ms):" -ForegroundColor White
    Write-Host "   $abaixo200/$($tempos.Count) endpoints ($([math]::Round($percentual, 1))%)" -ForegroundColor Gray
    
    if ($percentual -ge 95) {
        Write-Host "   ✅ META ATINGIDA! (>95%)" -ForegroundColor Green
    } elseif ($percentual -ge 80) {
        Write-Host "   ⚠️  Próximo da meta (80-95%)" -ForegroundColor Yellow
    } else {
        Write-Host "   ❌ Abaixo da meta (<80%)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host " 🎉 TESTES CONCLUÍDOS!" -ForegroundColor Yellow
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""
