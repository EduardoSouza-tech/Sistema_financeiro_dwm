# Teste simples do Railway
$BASE_URL = "https://sistema-financeiro-dwm-production.up.railway.app"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " TESTE RAILWAY - PRODUCAO" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Login
Write-Host "1. Fazendo login..." -ForegroundColor White
$loginBody = '{"email":"admin@dwm.com","senha":"admin123"}'

try {
    $login = Invoke-RestMethod -Uri "$BASE_URL/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = $login.token
    Write-Host "   OK - Token recebido" -ForegroundColor Green
}
catch {
    Write-Host "   ERRO: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Headers com token
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host ""
Write-Host "2. Testando endpoints..." -ForegroundColor White

# Dashboard
Write-Host "   Dashboard... " -NoNewline
$start = Get-Date
try {
    $dash = Invoke-RestMethod -Uri "$BASE_URL/api/relatorios/dashboard-completo" -Headers $headers
    $tempo = ((Get-Date) - $start).TotalMilliseconds
    Write-Host "OK ($([math]::Round($tempo))ms)" -ForegroundColor Green
}
catch {
    Write-Host "ERRO" -ForegroundColor Red
}

# Lancamentos
Write-Host "   Lancamentos... " -NoNewline
$start = Get-Date
try {
    $lanc = Invoke-RestMethod -Uri "$BASE_URL/api/lancamentos" -Headers $headers
    $tempo = ((Get-Date) - $start).TotalMilliseconds
    Write-Host "OK ($([math]::Round($tempo))ms)" -ForegroundColor Green
}
catch {
    Write-Host "ERRO" -ForegroundColor Red
}

# Clientes
Write-Host "   Clientes... " -NoNewline
$start = Get-Date
try {
    $cli = Invoke-RestMethod -Uri "$BASE_URL/api/clientes" -Headers $headers
    $tempo = ((Get-Date) - $start).TotalMilliseconds
    Write-Host "OK ($([math]::Round($tempo))ms)" -ForegroundColor Green
}
catch {
    Write-Host "ERRO" -ForegroundColor Red
}

# Contratos
Write-Host "   Contratos... " -NoNewline
$start = Get-Date
try {
    $cont = Invoke-RestMethod -Uri "$BASE_URL/api/contratos" -Headers $headers
    $tempo = ((Get-Date) - $start).TotalMilliseconds
    Write-Host "OK ($([math]::Round($tempo))ms)" -ForegroundColor Green
}
catch {
    Write-Host "ERRO" -ForegroundColor Red
}

# Performance stats
Write-Host ""
Write-Host "3. Performance stats..." -ForegroundColor White
try {
    $perf = Invoke-RestMethod -Uri "$BASE_URL/api/performance/stats" -Headers $headers
    
    if ($perf.cache) {
        Write-Host "   Cache: $($perf.cache.total_keys) chaves, $($perf.cache.hit_rate_percent)% hit rate" -ForegroundColor Cyan
    }
    
    if ($perf.queries) {
        $avgMs = [math]::Round($perf.queries.avg_time_ms, 2)
        Write-Host "   Queries: $($perf.queries.total_queries) executadas, $avgMs ms media" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "   ERRO: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " TESTES CONCLUIDOS!" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
