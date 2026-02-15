# Script para executar migration de associacao no Railway
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " EXECUTANDO MIGRATION: Coluna 'associacao' na tabela lancamentos" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Configurar envio de erros
$ErrorActionPreference = "Continue"

# Verificar se DATABASE_URL está configurado
if (-not $env:DATABASE_URL) {
    Write-Host "❌ ERRO: Variável DATABASE_URL não está configurada" -ForegroundColor Red
    Write-Host ""
    Write-Host "Configure a variável de ambiente DATABASE_URL com a URL do banco PostgreSQL Railway:" -ForegroundColor Yellow
    Write-Host '   $env:DATABASE_URL = "postgresql://user:pass@host:port/dbname"' -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "✅ DATABASE_URL encontrada" -ForegroundColor Green
Write-Host "   Host: " -NoNewline
$env:DATABASE_URL -match "postgres://(.+?)@(.+?)/" | Out-Null
Write-Host $Matches[2] -ForegroundColor Gray
Write-Host ""

# Encontrar Python
$pythonPath = $null

# Tentar Python no PATH
try {
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Path
} catch {}

if (-not $pythonPath) {
    try {
        $pythonPath = (Get-Command python3 -ErrorAction SilentlyContinue).Path
    } catch {}
}

# Tentar Python no .venv
if (-not $pythonPath) {
    $venvPython = "..\..venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $pythonPath = $venvPython
    }
}

if (-not $pythonPath) {
    Write-Host "❌ ERRO: Python não encontrado" -ForegroundColor Red
    Write-Host ""
    Write-Host "Certifique-se de que o Python está instalado e no PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Python encontrado: $pythonPath" -ForegroundColor Green
Write-Host ""

# Executar migration
Write-Host "🚀 Executando migration..." -ForegroundColor Cyan
Write-Host ""

& $pythonPath executar_migration_railway.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " ✅ MIGRATION CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "A coluna 'associacao' foi adicionada à tabela lancamentos no Railway" -ForegroundColor White
    Write-Host "O sistema agora está pronto para usar o campo de associação!" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " ❌ ERRO AO EXECUTAR MIGRATION" -ForegroundColor Red
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Verifique os logs acima para mais detalhes" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
