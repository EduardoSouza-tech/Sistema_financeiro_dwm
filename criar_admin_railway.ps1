# Script para criar usuário admin no Railway
$BASE_URL = "https://sistemafinanceirodwm-production.up.railway.app"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " CRIAR ADMIN NO RAILWAY" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Criando usuário admin..." -ForegroundColor White
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/debug/criar-admin" -Method Post -ContentType "application/json"
    
    Write-Host "   SUCESSO!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Credenciais criadas:" -ForegroundColor Cyan
    Write-Host "   Username: $($response.username)" -ForegroundColor White
    Write-Host "   Senha: $($response.senha)" -ForegroundColor White
    Write-Host "   Admin ID: $($response.admin_id)" -ForegroundColor Gray
    Write-Host ""
    
    # Testar login
    Write-Host "2. Testando login..." -ForegroundColor White
    $loginBody = "{`"username`":`"$($response.username)`",`"password`":`"$($response.senha)`"}"
    
    try {
        $login = Invoke-RestMethod -Uri "$BASE_URL/api/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
        Write-Host "   LOGIN OK!" -ForegroundColor Green
        Write-Host "   Token: $($login.token.Substring(0,40))..." -ForegroundColor Gray
    }
    catch {
        Write-Host "   Erro no login: $($_.Exception.Message)" -ForegroundColor Red
    }
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    
    if ($statusCode -eq 400) {
        Write-Host "   Admin já existe!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Credenciais:" -ForegroundColor Cyan
        Write-Host "   Username: admin" -ForegroundColor White
        Write-Host "   Senha: admin123" -ForegroundColor White
    }
    else {
        Write-Host "   ERRO: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Acesse: $BASE_URL" -ForegroundColor Cyan
Write-Host ""
