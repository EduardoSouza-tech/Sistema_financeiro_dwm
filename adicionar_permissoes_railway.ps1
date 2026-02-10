# Script para adicionar permissões de configuração de extrato
# Data: 2026-02-10

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "ADICIONANDO PERMISSÕES DE CONFIGURAÇÃO DE EXTRATO" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Obter DATABASE_URL do Railway
$DATABASE_URL = $env:DATABASE_URL

if (-not $DATABASE_URL) {
    Write-Host "❌ DATABASE_URL não encontrada!" -ForegroundColor Red
    Write-Host "Configure a variável de ambiente com o Railway" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ DATABASE_URL configurada" -ForegroundColor Green

# Extrair componentes da URL
if ($DATABASE_URL -match "postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)") {
    $DB_USER = $matches[1]
    $DB_PASS = $matches[2]
    $DB_HOST = $matches[3]
    $DB_PORT = $matches[4]
    $DB_NAME = $matches[5]
    
    Write-Host "📊 Banco: $DB_NAME @ $DB_HOST:$DB_PORT" -ForegroundColor Cyan
} else {
    Write-Host "❌ Formato de DATABASE_URL inválido!" -ForegroundColor Red
    exit 1
}

# Caminho do arquivo SQL
$SQL_FILE = Join-Path $PSScriptRoot "adicionar_permissoes_config_extrato.sql"

if (-not (Test-Path $SQL_FILE)) {
    Write-Host "❌ Arquivo SQL não encontrado: $SQL_FILE" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Arquivo SQL encontrado" -ForegroundColor Green
Write-Host ""

# Ler conteúdo do SQL
$SQL_CONTENT = Get-Content $SQL_FILE -Raw -Encoding UTF8

# Executar via psql (se disponível) ou via Python
$PYTHON_SCRIPT = @"
import psycopg2
import os

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cursor = conn.cursor()
    
    sql = '''$SQL_CONTENT'''
    
    cursor.execute(sql)
    conn.commit()
    
    print('✅ SQL executado com sucesso!')
    
    # Verificar resultado
    cursor.execute('''
        SELECT COUNT(*) 
        FROM usuario_empresas
        WHERE ativo = TRUE
        AND permissoes_empresa @> '["config_extrato_bancario_view"]'::jsonb
    ''')
    
    count = cursor.fetchone()[0]
    print(f'✅ {count} usuário(s) com permissões de config extrato')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Erro: {e}')
    exit(1)
"@

Write-Host "🔄 Executando SQL..." -ForegroundColor Yellow

# Salvar script Python temporário
$TEMP_PY = Join-Path $env:TEMP "add_permissions.py"
$PYTHON_SCRIPT | Out-File -FilePath $TEMP_PY -Encoding UTF8

# Executar
try {
    $env:DATABASE_URL = $DATABASE_URL
    python $TEMP_PY
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" * 80 -ForegroundColor Green
        Write-Host "✅ PERMISSÕES ADICIONADAS COM SUCESSO!" -ForegroundColor Green
        Write-Host "=" * 80 -ForegroundColor Green
        Write-Host ""
        Write-Host "🔄 Faça LOGOUT e LOGIN novamente para carregar as novas permissões" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Erro ao executar SQL" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Erro: $_" -ForegroundColor Red
} finally {
    Remove-Item $TEMP_PY -ErrorAction SilentlyContinue
}
